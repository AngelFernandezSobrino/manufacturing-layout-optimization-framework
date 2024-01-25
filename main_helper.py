from dataclasses import dataclass
from math import sqrt
from typing import List, Set

from networkx import Graph  # type: ignore
import model


@dataclass
class Position:
    x: int
    y: int

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    def __sub__(self, __value):
        return Position(self.x - __value.x, self.y - __value.y)

    def distance(self) -> float:
        return sqrt(self.x**2 + self.y**2)

    def dot_product(self, __value) -> float:
        return self.x * __value.x + self.y * __value.y


class Node:
    def __init__(
        self, station: model.StationModel, position: Position, previous_node
    ) -> None:
        self.station: model.StationModel = station
        self.position: Position = position
        self.next_nodes: List[Node] | None = None
        self.previous_node: Node | None = previous_node

    def __str__(self) -> str:
        return f"{self.station} {self.position}"


def create_plant_from_node(node: Node) -> model.PlantGridType:
    plant_grid: model.PlantGridType = [[None for x in range(5)] for y in range(5)]

    node_evaluated = node

    while True:
        plant_grid[node_evaluated.position.y][
            node_evaluated.position.x
        ] = node_evaluated.station

        if node_evaluated.previous_node is None:
            break

        node_evaluated = node_evaluated.previous_node

    return plant_grid


def create_plant_from_node_with_station_models_used(node: Node):
    plant_grid: model.PlantGridType = [[None for x in range(5)] for y in range(5)]
    station_models_used: Set = set()
    node_evaluated = node
    while True:
        plant_grid[node_evaluated.position.y][
            node_evaluated.position.x
        ] = node_evaluated.station

        station_models_used.add(node_evaluated.station.name)

        if node_evaluated.previous_node is None:
            break

        node_evaluated = node_evaluated.previous_node

    return plant_grid, station_models_used


def add_nodes(graph_generator: Graph, previous_node: Node, level: int, initial_x: int):
    if previous_node.next_nodes is None:
        return initial_x

    actual_x = initial_x

    for index, node in enumerate(previous_node.next_nodes):
        graph_generator.add_node(
            id(node),
            label=f"{node.station.name}:{node.position}",
            physics=False,
            x=actual_x * 60,
            y=level * 200 - index % 4 * 20,
        )
        graph_generator.add_edge(
            id(previous_node),
            id(node),
        )
        actual_x = add_nodes(graph_generator, node, level + 1, actual_x)
        actual_x += 1

    return actual_x


def get_robot_position(plant_grid: model.PlantGridType) -> Position:
    station_models = model.get_stations_model()

    for y in range(5):
        for x in range(5):
            if plant_grid[y][x] == station_models["Robot"]:
                return Position(x, y)

    raise Exception("Robot not found")


def check_configuration(plant_grid: model.PlantGridType) -> bool:
    robot_position = get_robot_position(plant_grid)
    station_models = model.get_stations_model()

    if (
        (
            robot_position.x > 0
            and plant_grid[robot_position.y][robot_position.x - 1]
            == station_models["Press"]
        )
        or (
            robot_position.x < 4
            and plant_grid[robot_position.y][robot_position.x + 1]
            == station_models["Press"]
        )
        or (
            robot_position.y > 0
            and plant_grid[robot_position.y - 1][robot_position.x]
            == station_models["Press"]
        )
        or (
            robot_position.y < 4
            and plant_grid[robot_position.y + 1][robot_position.x]
            == station_models["Press"]
            or (
                robot_position.x > 0
                and robot_position.y > 0
                and plant_grid[robot_position.y - 1][robot_position.x - 1]
                == station_models["Press"]
            )
            or (
                robot_position.x < 4
                and robot_position.y > 0
                and plant_grid[robot_position.y - 1][robot_position.x + 1]
                == station_models["Press"]
            )
            or (
                robot_position.x > 0
                and robot_position.y < 4
                and plant_grid[robot_position.y + 1][robot_position.x - 1]
                == station_models["Press"]
            )
            or (
                robot_position.x < 4
                and robot_position.y < 4
                and plant_grid[robot_position.y + 1][robot_position.x + 1]
                == station_models["Press"]
            )
        )
    ):
        if (
            (
                robot_position.x > 0
                and plant_grid[robot_position.y][robot_position.x - 1]
                == station_models["InOut"]
            )
            or (
                robot_position.x < 4
                and plant_grid[robot_position.y][robot_position.x + 1]
                == station_models["InOut"]
            )
            or (
                robot_position.y > 0
                and plant_grid[robot_position.y - 1][robot_position.x]
                == station_models["InOut"]
            )
            or (
                robot_position.y < 4
                and plant_grid[robot_position.y + 1][robot_position.x]
                == station_models["InOut"]
                or (
                    robot_position.x > 0
                    and robot_position.y > 0
                    and plant_grid[robot_position.y - 1][robot_position.x - 1]
                    == station_models["InOut"]
                )
                or (
                    robot_position.x < 4
                    and robot_position.y > 0
                    and plant_grid[robot_position.y - 1][robot_position.x + 1]
                    == station_models["InOut"]
                )
                or (
                    robot_position.x > 0
                    and robot_position.y < 4
                    and plant_grid[robot_position.y + 1][robot_position.x - 1]
                    == station_models["InOut"]
                )
                or (
                    robot_position.x < 4
                    and robot_position.y < 4
                    and plant_grid[robot_position.y + 1][robot_position.x + 1]
                    == station_models["InOut"]
                )
            )
        ):
            return True
        else:
            return False
    else:
        return False


# Now we have the function to check if a configuration is valid or not, we can check all the configurations
