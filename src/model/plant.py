from __future__ import annotations

import copy
from dataclasses import dataclass
import itertools
from math import atan2, cos, sin, sqrt
import sys
from turtle import pos
from typing import List, Optional
import matplotlib
from matplotlib.figure import Figure
import prettytable
import pyvisgraph as vg

import shapely
import shapely.ops

from model import GridParams, StationModel, StationNameType, Vector
from model.tools import SystemSpecification

"""Plant description

Coordinates

    ┌────► x 
    │        
    │        
    ▼        
    y        

Station coordinates
    
    ┌───────┐ ──▲        
    │       │   │        
    │       │   │x length
    │       │   │        
    └───────┘ ──▼        
                        
    │       │            
    ◄───────►            
    y length           

    ───────► x 
    0,0         
    │  ┌───────┐  
    │  │       │  
    │  │       │  
    │  │       │  
    ▼  └───────┘  
    y             

Grid coordinates

    0,0 ───────► x
      ┌──────┬──────┬──────┐ 
    │ │      │      │      │ 
    │ │ 0,0  │ 1,0  │ 2,0  │ 
    │ ├──────┼──────┼──────┤ 
    │ │      │      │      │ 
    │ │ 0,1  │ 1,1  │ 2,1  │ 
    ▼ ├──────┼──────┼──────┤ 
    y │      │      │      │ 
      │ 0,2  │ 1,2  │ 2,2  │ 
      └──────┴──────┴──────┘ 
"""


class Plant:
    def __init__(self, system_spec: SystemSpecification) -> None:
        """Model of the 2D distribution of the stations in the plant

        It requires to be associated to a system specification to configure the plant data structure. Furthermore, the spec models are referenced in the plant distribution data structure, so the stations models can be directly accessed from the plant data structure.

        It implements the iterator protocol to iterate over the plant stations. The iterator returns a tuple with the position of the station and the station model.

        It can't be used until the ready method is called, as it is used to signal that the plant modelsg

        """

        self._grid_params = system_spec.model.stations.grid

        self._system_spec = system_spec
        self._config: list[tuple[Vector[int], StationNameType]] = []

        self._grid: list[list[Optional[StationModel]]] = [
            [None for x in range(self._grid_params.size.x)]
            for y in range(self._grid_params.size.y)
        ]

        self._not_ready = True

        self._poligons: PlantPoligonsPoints = PlantPoligonsPoints([], {})
        self._vis_graphs: dict[StationNameType, vg.VisGraph] = {}

    def __iter__(self):
        self._iter_x = -1
        self._iter_y = -1
        return self

    def __next__(self) -> tuple[Vector[int], StationModel]:
        self._iter_x += 1
        if self._iter_x == self._grid_params.size.x:
            self._iter_x = 0
            self._iter_y += 1
            if self._iter_y == self._grid_params.size.y:
                raise StopIteration

        actual = self._grid[self._iter_y][self._iter_x]

        return (
            (Vector(self._iter_x, self._iter_y), actual)
            if actual is not None
            else self.__next__()
        )

    def set_location(self, position: Vector[int], station: StationModel):
        self._grid[position.y][position.x] = station

    def get_and_remove(self, position: Vector[int]) -> StationModel:
        station = self._grid[position.y][position.x]
        self._grid[position.y][position.x] = None
        assert station is not None
        return station

    def get_and_remove_coord(self, x: int, y: int) -> StationModel:
        station = self._grid[y][x]
        assert station is not None, f"Station at {x},{y} is None"
        self._grid[y][x] = None
        return station

    def is_empty_coord(self, x: int, y: int):
        return self._grid[y][x] is None

    def get_location(self, position: Vector[int]) -> Optional[StationModel]:
        return self._grid[position.y][position.x]

    def get_location_coordinates(self, x: int, y: int) -> Optional[StationModel]:
        return self._grid[y][x]

    def ready(self):
        self._not_ready = False

    def search_by_name(self, station_name: StationNameType):
        for x, y in itertools.product(
            range(self._grid_params.size.x), range(self._grid_params.size.y)
        ):
            if self._grid[y][x] is None:
                continue

            if self._grid[y][x].name == station_name:
                return Vector(x, y)

        raise ValueError(f"Station {station_name} not found")

    def build_vis_graphs(self):

        assert not self._not_ready

        # Compute the poligons that are going to be used to build the visibility graph
        for x, y in itertools.product(
            range(self._grid_params.size.x), range(self._grid_params.size.y)
        ):

            station = self._grid[y][x]

            if station is None:
                continue
            if station.obstacles is None:
                continue
            if station.transports is None:
                self._poligons.normal.extend(
                    station.get_absolute_obstacles(
                        Vector(
                            x * self._grid_params.measures.x,
                            y * self._grid_params.measures.y,
                        )
                    )
                )
            else:
                self._poligons.robot[station.name] = station.get_absolute_obstacles(
                    Vector(
                        x * self._grid_params.measures.x,
                        y * self._grid_params.measures.y,
                    )
                )

        # Compute the visibility graph for each transport station
        for x, y in itertools.product(
            range(self._grid_params.size.x), range(self._grid_params.size.y)
        ):
            station = self._grid[y][x]
            if station is None:
                continue
            if station.transports is None:
                continue

            self._build_transport_visibility_graph(
                Vector(
                    self._grid_params.half_measures.x
                    + x * self._grid_params.measures.x,
                    self._grid_params.half_measures.y
                    + y * self._grid_params.measures.y,
                ),
                station.name,
            )

    def _build_transport_visibility_graph(
        self, station_position: Vector[float], station_name: str
    ):

        self._vis_graphs[station_name] = vg.VisGraph()

        # List of all other poligons that are not from the current transport station
        all_other_poligons: list[list[vg.Point]] = [
            p for p in self._poligons.normal
        ] + [
            p
            for poligon_station_name, poligons in self._poligons.robot.items()
            for p in poligons
            if poligon_station_name != station_name
        ]

        # Visibility graph that will be used to find the visible vertices from the transport station
        visibility_graph = vg.VisGraph()

        # Visible vertices from the transport station repo
        visible_points: list[vg.Point] = []

        # Find the visible vertices from the transport station for each of the poligons independently
        for p in all_other_poligons:
            visibility_graph.build([p], workers=1, status=False)
            visible_points.extend(
                visibility_graph.find_visible(
                    vg.Point(station_position.x, station_position.y)
                )
            )

        # To avoid the poligons that are not visible from the transport station to be used, the region behind the poligons has to be increased in size to be sure that any path that goes through these vertices is not going to be used
        # To do that we need to find the angle between the transport station and the vertices of the poligons, and then we will move the vertices in the direction of the angle by a fixed distance of 20 units

        # Theses poligons are the same than all other poligons, but with the vertices that are not visible from the transport station moved to the direction of the angle between the transport station and the vertex
        final_poligons: list[list[vg.Point]] = []

        for poligon in all_other_poligons:
            new_poligon: list[vg.Point] = []
            final_poligons.append(new_poligon)
            for index, point in enumerate(poligon):
                last = index - 1 if index > 0 else len(poligon) - 1
                next = index + 1 if index < len(poligon) - 1 else 0

                if point in visible_points:
                    next_not_visible = poligon[next] not in visible_points
                    last_not_visible = poligon[last] not in visible_points
                    if next_not_visible:
                        angle = angle_between_two_points(
                            station_position.x, station_position.y, point
                        )
                        new_poligon.append(point)
                        new_poligon.append(
                            vg.Point(
                                point.x + 20 * cos(angle), point.y + 20 * sin(angle)
                            )
                        )
                    elif last_not_visible:
                        angle = angle_between_two_points(
                            station_position.x, station_position.y, point
                        )
                        new_poligon.append(
                            vg.Point(
                                point.x + 20 * cos(angle), point.y + 20 * sin(angle)
                            )
                        )
                        new_poligon.append(point)
                    else:
                        new_poligon.append(point)

        # These poligons could now intersect, so we have to merge them
        # First we have to convert them to shapely poligons
        shapely_poligons = [
            shapely.Polygon([(point.x, point.y) for point in poligon])
            for poligon in final_poligons
        ]

        shapely_poligons_union = shapely.union_all(shapely_poligons, grid_size=0.1)

        # Once the poligons are merged, we have to convert them back to the format that the visibility graph can use
        # If the merge process returns only one poligon we will convert it to a multipoligon (just and array of poligons), to simplify the conversion later.
        if isinstance(shapely_poligons_union, shapely.Polygon):
            # print("Overlaped stuff")
            shapely_poligons_union = shapely.MultiPolygon([shapely_poligons_union])

        new_poligons = [
            [vg.Point(x, y) for x, y in shapely_poligon.exterior.coords]
            for shapely_poligon in shapely_poligons_union.geoms
        ]

        # We are going to remove the last point of each poligon, as it is the same as the first point
        for poligon in new_poligons:
            poligon.pop()

        self._vis_graphs[station_name].build(new_poligons, workers=1, status=False)

    def hash(self):
        plant_hash = ""

        for y, x in itertools.product(
            range(self._grid_params.size.y), range(self._grid_params.size.x)
        ):
            if self._grid[y][x] is None:
                continue
            plant_hash += f"{self._grid[y][x].name}({x},{y})"  # type: ignore

        return plant_hash

    def _update_config(self):
        for y, x in itertools.product(
            range(self._grid_params.size.y), range(self._grid_params.size.x)
        ):
            if self._grid[y][x] is None:
                continue
            self._config.append((Vector(x, y), self._grid[y][x].name))  # type: ignore

    def export_config(self):
        self._update_config()
        return self._config

    def import_config(self, config: PlantConfigType):
        self._config = copy.deepcopy(config)
        for position, station_name in self._config:
            self.set_location(
                position, self._system_spec.model.stations.models[station_name]
            )

    def get_path_between_two_points_with_transport(
        self, point1: Vector[float], point2: Vector[float], transport_name: str
    ) -> List[vg.Point]:

        return self._vis_graphs[transport_name].shortest_path(
            vg.Point(point1.x, point1.y), vg.Point(point2.x, point2.y)
        )

    def get_flat_config_set(self):

        hash_set: set[str] = set()

        for x, y in itertools.product(
            range(self._grid_params.size.x), range(self._grid_params.size.y)
        ):
            if self._grid[y][x] is None:
                continue

            hash_set.add(f"{self._grid[y][x].name}({x},{y})")

        return hash_set

    def print(self, width=15):
        table = prettytable.PrettyTable()
        column_names = ["", "0", "1", "2", "3", "4"]
        table_width: dict[str, int] = {}

        for name in column_names:
            table_width[name] = width

        table.field_names = column_names
        table._max_width = table_width
        table._min_width = table_width

        for row_index, row in enumerate(self._grid):
            table.add_row([row_index, *row])

        print(table)

    def plot_plant_graph(self):
        import matplotlib.pyplot as plt
        import matplotlib.axes
        import matplotlib.ticker
        import pyvisgraph as vg

        visibility_graph = vg.VisGraph()

        all_poligons = [poligon for poligon in self._poligons.normal] + [
            poligon
            for robot_name, poligons in self._poligons.robot.items()
            for poligon in poligons
        ]

        visibility_graph.build(
            all_poligons,
            workers=1,
            status=False,
        )

        # Create matplotlib axes without figure

        fig = plt.figure()

        vis_axes = fig.add_subplot(1, len(self._vis_graphs) + 1, 1)

        axes_dict: dict[StationNameType, matplotlib.axes.Axes] = {
            station_name: fig.add_subplot(1, len(self._vis_graphs) + 1, index + 2)
            for index, station_name in enumerate(self._vis_graphs)
        }

        if visibility_graph.graph is not None:
            for edge in visibility_graph.graph.get_edges():
                vis_axes.plot(
                    [edge.p1.x, edge.p2.x], [edge.p1.y, edge.p2.y], color="blue"
                )

        vis_axes.set_aspect("equal")
        vis_axes.set_xlim(0, self._grid_params.measures.x * self._grid_params.size.x)
        vis_axes.set_ylim(0, self._grid_params.measures.y * self._grid_params.size.y)
        vis_axes.xaxis.set_major_locator(
            matplotlib.ticker.MultipleLocator(self._grid_params.measures.x)
        )
        vis_axes.yaxis.set_major_locator(
            matplotlib.ticker.MultipleLocator(self._grid_params.measures.y)
        )
        vis_axes.invert_yaxis()
        vis_axes.grid(True, which="major", linestyle="-", linewidth=0.5)
        vis_axes.grid(True, which="minor", linestyle=":", linewidth=0.2)

        for (transport_station_name, vis_graph), axes in zip(
            self._vis_graphs.items(), axes_dict.values()
        ):
            if vis_graph.graph is None or vis_graph.visgraph is None:
                continue

            for edge in vis_graph.graph.get_edges():
                axes.plot([edge.p1.x, edge.p2.x], [edge.p1.y, edge.p2.y], color="blue")

            # Plot a point in axes representing the transport station position
            # Get transport station position
            transport_station_position = self.search_by_name(transport_station_name)

            axes.plot(
                self._grid_params.half_measures.x
                + transport_station_position.x * self._grid_params.measures.x,
                self._grid_params.half_measures.y
                + transport_station_position.y * self._grid_params.measures.y,
                "ro",
            )

            axes.set_aspect("equal")

            axes.set_xlim(0, self._grid_params.measures.x * self._grid_params.size.x)
            axes.set_ylim(0, self._grid_params.measures.y * self._grid_params.size.y)
            axes.xaxis.set_major_locator(
                matplotlib.ticker.MultipleLocator(self._grid_params.measures.x)
            )
            axes.yaxis.set_major_locator(
                matplotlib.ticker.MultipleLocator(self._grid_params.measures.y)
            )
            axes.invert_yaxis()
            axes.grid(True, which="major", linestyle="-", linewidth=0.5)
            axes.grid(True, which="minor", linestyle=":", linewidth=0.2)

        return fig, axes_dict, vis_axes

    def compare(self, other: Plant):
        """Gets another plant and compares it with the current plant

        It returns a grid array with the comparison of the two plants. If the two plants have the same content at an specific position, the value at that position is True, otherwise it is False.

        Args:
            other (Plant): _description_

        Returns:
            bool: _description_
        """
        result: list[list[bool]] = [
            [False for x in range(self._grid_params.size.x)]
            for y in range(self._grid_params.size.y)
        ]

        for y, x in itertools.product(
            range(self._grid_params.size.y), range(self._grid_params.size.x)
        ):
            if self._grid[y][x] is None and other._grid[y][x] is None:
                result[y][x] = True
            elif self._grid[y][x] is not None and other._grid[y][x] is not None:
                result[y][x] = self._grid[y][x].name == other._grid[y][x].name

        return result


PlantConfigType = list[tuple[Vector[int], StationNameType]]


@dataclass
class PlantPoligonsPoints:
    normal: list[list[vg.Point]]
    robot: dict[str, list[list[vg.Point]]]


def angle_between_two_points(
    point1_x: float, point1_y: float, point2: vg.Point
) -> float:
    return atan2(point2.y - point1_y, point2.x - point1_x)


def path_distance(path: List[vg.Point]) -> float:
    distance = 0
    for i in range(len(path) - 1):
        distance += sqrt(
            (path[i].x - path[i + 1].x) ** 2 + (path[i].y - path[i + 1].y) ** 2
        )
    return distance


class RearrangmentPlant(Plant):
    def __init__(self, system_spec: SystemSpecification) -> None:
        super().__init__(system_spec)

    def move_station_to_another_coord(self, x1: int, y1: int, x2: int, y2):
        """Moves a station from one position to another

        It will check if the movement is possible and then move the station to the new position
        """
        for x in range(self._grid_params.size.x - 1, x2, -1):
            if self._grid[y2][x] is None:
                continue
            raise UnsolvableError(f"Station at {x2},{y2} is not None")

        station = self._grid[y1][x1]
        assert station is not None, f"Station at {x1},{y1} is None"
        self._grid[y2][x2] = station
        self._grid[y1][x1] = None

        return station.name


class RearrangmentPlantV1(RearrangmentPlant):
    def __init__(self, system_spec: SystemSpecification) -> None:
        super().__init__(system_spec)
        self.storage_buffer: list[StationModel | None] = []

    def move_station_to_storage_buffer_coord(self, x: int, y: int):
        """Moves a station from the plant to the storage buffer

        Returns the number of stations in the storage buffer
        """
        station = self._grid[y][x]
        assert station is not None, f"Station at {x},{y} is None"
        self.storage_buffer.append(station)
        self._grid[y][x] = None
        return self.storage_buffer[-1].name, len(self.storage_buffer)

    def move_station_from_buffer_to_coord(
        self, station_name: StationNameType, x: int, y: int
    ):
        assert self._grid[y][x] is None, f"Station at {x},{y} is not None"

        for index, station in enumerate(self.storage_buffer):
            if station is not None and station.name == station_name:
                self._grid[y][x] = self.storage_buffer[index]
                self.storage_buffer[index] = None
                return index


class RearrangmentPlantV2(RearrangmentPlant):
    def __init__(self, system_spec: SystemSpecification, buffer_size: int) -> None:
        super().__init__(system_spec)
        self.storage_buffer: list[StationModel | None] = [
            None for _ in range(buffer_size)
        ]

        self.storage_buffer_cursor: int = 0

    def move_station_to_storage_buffer_coord(self, x: int, y: int):
        """Moves a station from the plant to the storage buffer

        Returns the number of stations in the storage buffer
        """
        if self.storage_buffer_cursor >= len(self.storage_buffer):
            raise UnsolvableError("Storage buffer is not big enough")

        station = self._grid[y][x]
        assert station is not None, f"Station at {x},{y} is None"
        result = station.name, self.storage_buffer_cursor + 1

        self.storage_buffer[self.storage_buffer_cursor] = station
        self._grid[y][x] = None
        self.storage_buffer_cursor += 1

        while True:
            if self.storage_buffer_cursor == len(self.storage_buffer):
                break

            if self.storage_buffer[self.storage_buffer_cursor] is not None:
                self.storage_buffer_cursor += 1
            else:
                break

        return result

    def move_station_from_buffer_to_coord(
        self, station_name: StationNameType, x: int, y: int
    ):
        assert self._grid[y][x] is None, f"Station at {x},{y} is not None"

        for index, station in enumerate(self.storage_buffer):
            if station is not None and station.name == station_name:
                self._grid[y][x] = self.storage_buffer[index]
                self.storage_buffer[index] = None
                self.storage_buffer_cursor = index
                return index


class UnsolvableError(Exception):
    pass
