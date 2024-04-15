import copy
from dataclasses import dataclass
import itertools
from math import atan2, cos, sin, sqrt
from typing import List, Optional
import matplotlib
from matplotlib.figure import Figure
import prettytable
import pyvisgraph as vg

from model import Grid, StationModel, StationNameType, Vector
from model import GridParams, StationModel, StationNameType, Vector


class Plant:
    def __init__(self, grid: GridParams) -> None:

        self.grid_params = grid

        self.grid: list[list[Optional[StationModel]]] = [
            [None for x in range(self.grid_params.size.x)]
            for y in range(self.grid_params.size.y)
        ]

        self.empty = True

        self.poligons: PlantPoligonsPoints = PlantPoligonsPoints([], {})
        self.vis_graphs: dict[StationNameType, vg.VisGraph] = {}

    def build_vis_graphs(self):

        assert not self.empty

        # Compute the poligons that are going to be used to build the visibility graph
        for x, y in itertools.product(
            range(self.grid_params.size.x), range(self.grid_params.size.y)
        ):

            station = self.grid[y][x]

            if station is None:
                continue
            if station.obstacles is None:
                continue
            if station.transports is None:
                self.poligons.poligons.extend(station.obstacles)
            else:
                self.poligons.robot_poligons[station.name] = station.obstacles

        # Compute the visibility graph for each transport station
        for x, y in itertools.product(
            range(self.grid_params.size.x), range(self.grid_params.size.y)
        ):
            station = self.grid[y][x]
            if station is None:
                continue
            if station.transports is None:
                continue

            self._build_transport_visibility_graph(Vector(x, y), station.name)

    def _build_transport_visibility_graph(
        self, station_position: Vector[int], station_name: str
    ):

        # Create a visibility graph considering all the poligons except the ones that are associated with that transport station

        visibility_graph = vg.VisGraph()

        visibility_graph.build(
            [poligon for poligon in self.poligons.poligons]
            + [
                poligon
                for robot_name, poligons in self.poligons.robot_poligons.items()
                if robot_name != station_name
                for poligon in poligons
            ],
            workers=1,
            status=False,
        )

        # Create the robot visibility graph
        self.vis_graphs[station_name] = vg.VisGraph()

        # Check the vertices that are visible from the transport station in the local visibility graph
        visible_vertices = visibility_graph.find_visible(
            vg.Point(station_position.x, station_position.y)
        )

        new_poligons = copy.deepcopy(self.poligons)

        # To avoid the poligons that are not visible from the transport station to be used, the region behind the poligons has to be increased in size to be sure that any path that goes through these vertices is not going to be used
        # To do that we need to find the angle between the transport station and the vertices of the poligons, and then we will move the vertices in the direction of the angle by a fixed distance of 20 units

        for poligon in new_poligons.poligons:
            for point in poligon:
                if point in visible_vertices:
                    continue
                angle = angle_between_two_points(
                    station_position.x, station_position.y, point
                )
                point.x += 20 * cos(angle)
                point.y += 20 * sin(angle)

        for robot_name, poligons in new_poligons.robot_poligons.items():
            if robot_name == station_name:
                continue
            for poligon in poligons:
                for point in poligon:
                    if point in visible_vertices:
                        continue
                    angle = angle_between_two_points(
                        station_position.x, station_position.y, point
                    )
                    point.x += 20 * cos(angle)
                    point.y += 20 * sin(angle)

        self.vis_graphs[station_name].build(
            [poligon for poligon in new_poligons.poligons]
            + [
                poligon
                for robot_name, poligons in new_poligons.robot_poligons.items()
                for poligon in poligons
            ],
            workers=1,
            status=False,
        )

    def hash(self):
        plant_hash = ""
        for y in range(self.grid_params.size.y):
            for x in range(self.grid_params.size.x):
                if self.grid[y][x] is None:
                    continue
                plant_hash += f"{self.grid[y][x].name}({x},{y})"  # type: ignore

        return plant_hash

    def get_path_between_two_points_with_transport(
        self, point1: Vector[float], point2: Vector[float], transport_name: str
    ) -> List[vg.Point]:

        return self.vis_graphs[transport_name].shortest_path(
            vg.Point(point1.x, point1.y), vg.Point(point2.x, point2.y)
        )

    def print(self, width=15):
        table = prettytable.PrettyTable()
        column_names = ["", "0", "1", "2", "3", "4"]
        table_width: dict[str, int] = {}

        for name in column_names:
            table_width[name] = width

        table.field_names = column_names
        table._max_width = table_width
        table._min_width = table_width

        for row_index, row in enumerate(self.grid):
            table.add_row([row_index, *row])

        print(table)

    def populated(self):
        self.empty = False

    def plot_plant_graph(self):
        import matplotlib.pyplot as plt
        import matplotlib.axes
        import pyvisgraph as vg

        axes_dict: dict[StationNameType, matplotlib.axes.Axes] = {
            station_name: plt.axes() for station_name in self.vis_graphs.keys()
        }

        for (transport_station_name, vis_graph), axes in zip(
            self.vis_graphs.items(), axes_dict.values()
        ):
            if vis_graph.graph is None or vis_graph.visgraph is None:
                continue

            for edge in vis_graph.visgraph.get_edges():
                print("Ploting edge", edge.p1, edge.p2)
                plt.plot([edge.p1.x, edge.p2.x], [edge.p1.y, edge.p2.y], color="blue")

            path_x = []
            path_y = []

            for point in vis_graph.shortest_path(
                vg.Point(0, 0), destination=vg.Point(2, 2)
            ):
                path_x.append(point.x)
                path_y.append(point.y)

            print("Plotting path: ", path_x, path_y)

            assert isinstance(axes, matplotlib.axes.Axes)

            axes.plot(path_x, path_y, color="blue")
kraken
            axes.set_xlim(0, 5)
            axes.set_ylim(0, 5)

        return axes_dict


@dataclass
class PlantPoligonsPoints:
    poligons: list[list[vg.Point]]
    robot_poligons: dict[str, list[list[vg.Point]]]


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
