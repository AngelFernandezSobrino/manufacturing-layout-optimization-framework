from dataclasses import dataclass
from math import sqrt
from typing import Dict, List, Set

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


def get_available_positions(
    plant_grid: model.PlantGridType,
) -> tuple[List[Position], List[List[int]]]:
    available_positions_array: List[Position] = []
    available_positions_grid: List[List[int]] = [
        [0 for x in range(5)] for y in range(5)
    ]

    for y in range(1, 5):
        for x in range(5):
            if plant_grid[y][x] is None:
                if (
                    (plant_grid[y - 1][x] is not None)
                    or (x > 0 and plant_grid[y][x - 1] is not None)
                    or (x < 4 and plant_grid[y][x + 1] is not None)
                    or (y < 4 and plant_grid[y + 1][x] is not None)
                    or (x > 0 and plant_grid[y - 1][x - 1] is not None)
                    or (x < 4 and plant_grid[y - 1][x + 1] is not None)
                    or (y < 4 and x > 0 and plant_grid[y + 1][x - 1] is not None)
                    or (y < 4 and x < 4 and plant_grid[y + 1][x + 1] is not None)
                ):
                    available_positions_grid[y][x] = 1
                    available_positions_array.append(Position(x, y))

    return available_positions_array, available_positions_grid


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


def evaluate_robot_penalties(robot: Position, origin: Position, destiny: Position):
    robot_to_origin = robot - origin
    robot_to_destiny = robot - destiny
    origin_to_destiny = origin - destiny

    return (
        abs(robot_to_origin.dot_product(robot_to_destiny))
        / origin_to_destiny.distance()
    )


import graphs


def check_performace(plant_grid: model.PlantGridType) -> float:
    robot_position: Position = get_robot_position(plant_grid)

    node_positions: Dict[node.name, Position] = {}

    result = 0

    for node in graphs.nodes_v2:
        for colIndex, column in enumerate(plant_grid):
            for rowIndex, station in enumerate(iterable=column):
                if station is None:
                    continue
                if station.name == node.station.name:
                    node_positions[node.station.name] = Position(colIndex, rowIndex)

    for node in graphs.nodes_v2:
        for edge in node.outgoing_edges:
            stations_distance = (
                node_positions[edge.destination.station.name]
                - node_positions[node.station.name]
            ).distance()
            robot_distance_origin = (
                robot_position - node_positions[node.station.name]
            ).distance()
            robot_distance_destiny = (
                robot_position - node_positions[edge.destination.station.name]
            ).distance()
            position_penalty = evaluate_robot_penalties(
                robot_position,
                node_positions[node.station.name],
                node_positions[edge.destination.station.name],
            )

            result += (
                stations_distance
                + robot_distance_origin / 4
                + robot_distance_destiny / 4
                + position_penalty
            )

    return result
