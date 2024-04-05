import copy
import itertools
from math import atan2, cos, sin, sqrt
from typing import List, Optional
import prettytable
import pyvisgraph as vg

from model import Grid, StationModel, Vector


class Plant:
    def __init__(self, grid: Grid) -> None:

        self.grid_params = grid

        self.grid: list[list[Optional[StationModel]]] = [
            [None for x in range(self.grid_params.size.x)]
            for y in range(self.grid_params.size.y)
        ]

        self.vis_graph: vg.VisGraph = vg.VisGraph()

        # We need to create a custom visibility graph for each transport station in the plant

        self.transport_vis_graphs: dict[str, vg.VisGraph] = {}

    def build_visibility_graphs(self):
        self.vis_graph = vg.VisGraph()
        self.poligons: List[List[vg.Point]] = []
        for x, y in itertools.product(
            range(self.grid_params.size.x), range(self.grid_params.size.y)
        ):

            station = self.grid[y][x]
            if station is None:
                continue
            if station.obstacles is None:
                continue

            for obstacle in station.obstacles:
                north = vg.Point(
                    float(
                        x * self.grid_params.measures.x
                        + obstacle.center.x
                        + obstacle.size.x / 2
                    ),
                    float(
                        y * self.grid_params.measures.y
                        + obstacle.center.y
                        + obstacle.size.y / 2
                    ),
                )
                south = vg.Point(
                    float(
                        x * self.grid_params.measures.x
                        + obstacle.center.x
                        - obstacle.size.x / 2
                    ),
                    float(
                        y * self.grid_params.measures.y
                        + obstacle.center.y
                        - obstacle.size.y / 2
                    ),
                )
                east = vg.Point(
                    float(
                        x * self.grid_params.measures.x
                        + obstacle.center.x
                        + obstacle.size.x / 2
                    ),
                    float(
                        y * self.grid_params.measures.y
                        + obstacle.center.y
                        - obstacle.size.y / 2
                    ),
                )
                west = vg.Point(
                    float(
                        x * self.grid_params.measures.x
                        + obstacle.center.x
                        - obstacle.size.x / 2
                    ),
                    float(
                        y * self.grid_params.measures.y
                        + obstacle.center.y
                        + obstacle.size.y / 2
                    ),
                )
                self.poligons.append([north, east, south, west])

        self.vis_graph.build(self.poligons, workers=1, status=False)

        self.print()

        for x, y in itertools.product(
            range(self.grid_params.size.x), range(self.grid_params.size.y)
        ):
            station = self.grid[y][x]
            if station is None:
                continue
            if station.transports is None:
                continue

            self.build_transport_visibility_graph(Vector(x, y), station.name)

    def build_transport_visibility_graph(
        self, station_position: Vector[int], station_name: str
    ):
        self.transport_vis_graphs[station_name] = vg.VisGraph()
        # We are going to find the poligons that are visible from the transport station
        visible_vertices = self.vis_graph.find_visible(
            vg.Point(station_position.x, station_position.y)
        )
        new_poligons = copy.deepcopy(self.poligons)
        # To avoid the poligons that are not visible from the transport station to be used, the region behind the poligons has to be increased in size to be sure that any path that goes through these vertices is not going to be used

        # To do that we need to find the angle between the transport station and the vertices of the poligons, and then we will move the vertices in the direction of the angle by a fixed distance of 20 units

        for poligon in new_poligons:
            for vertex in poligon:
                if vertex in visible_vertices:
                    continue
                angle = angle_between_two_points(
                    vg.Point(station_position.x, station_position.y), vertex
                )
                vertex.x += 20 * cos(angle)
                vertex.y += 20 * sin(angle)

        self.transport_vis_graphs[station_name].build(
            new_poligons, workers=1, status=False
        )
        print(self.transport_vis_graphs)

    def hash(self):
        plant_hash = ""
        for y in range(self.grid_params.size.y):
            for x in range(self.grid_params.size.x):
                if self.grid[y][x] is None:
                    continue
                plant_hash += f"{self.grid[y][x].name}({x},{y})"  # type: ignore

        return plant_hash

    def get_path_between_two_points_transport(
        self, point1: Vector[float], point2: Vector[float], transport_name: str
    ) -> List[vg.Point]:

        return self.transport_vis_graphs[transport_name].shortest_path(
            vg.Point(point1.x, point1.y), vg.Point(point2.x, point2.y)
        )

    def get_shortest_path_lenght_between_two_points_using_transport(
        self, point1: Vector[float], point2: Vector[float], transport_name: str
    ) -> float:
        return path_distance(
            self.get_path_between_two_points_transport(point1, point2, transport_name)
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


def angle_between_two_points(point1: vg.Point, point2: vg.Point) -> float:
    return atan2(point2.y - point1.y, point2.x - point1.x)


def path_distance(path: List[vg.Point]) -> float:
    distance = 0
    for i in range(len(path) - 1):
        distance += sqrt(
            (path[i].x - path[i + 1].x) ** 2 + (path[i].y - path[i + 1].y) ** 2
        )
    return distance
