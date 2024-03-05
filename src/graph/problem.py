from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
import re
from typing import Dict, List, Set

from graph.process import ManufacturingProcessGraph
from model import tools

from . import (
    TreeNode,
    ProcessGraphNode,
    ProcessGraphEdge,
    ProcessGraphEdgeWithTransport,
)

from model import Vector, PlantGridType, StationModel


def create_plant_from_node_with_station_models_used(node: TreeNode):
    plant_grid: PlantGridType = tools.get_void_plant_grid()
    station_models_used: Set = set()
    node_evaluated = node
    while True:
        plant_grid[node_evaluated.position.y][
            node_evaluated.position.x
        ] = node_evaluated.station

        station_models_used.add(node_evaluated.station.name)

        if node_evaluated.previous is None:
            break

        node_evaluated = node_evaluated.previous

    return plant_grid, station_models_used


def get_available_positions(
    plant_grid: PlantGridType,
) -> tuple[List[Vector], List[List[int]]]:
    available_Vectors_array: List[Vector] = []
    available_Vectors_grid: List[List[int]] = [[0 for x in range(5)] for y in range(5)]

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
                    available_Vectors_grid[y][x] = 1
                    available_Vectors_array.append(Vector(x, y))

    return available_Vectors_array, available_Vectors_grid


def get_stations_with_transport_vectors(
    plant_grid: PlantGridType,
) -> List[Vector]:

    transport_vectors: List[Vector] = []

    for y in range(5):
        for x in range(5):
            station = plant_grid[y][x]
            if station is None:
                continue
            if station.transport is not None:
                transport_vectors.append(Vector(x, y))

    if len(transport_vectors) > 0:
        return transport_vectors

    raise Exception("Robot not found")


def check_configuration(plant_grid: PlantGridType) -> bool:
    robot_vectors = get_stations_with_transport_vectors(plant_grid)
    return True


# Now we have the function to check if a configuration is valid or not, we can check all the configurations


def evaluate_robot_penalties(robot: Vector, origin: Vector, destiny: Vector):
    robot_to_origin = robot - origin
    robot_to_destiny = robot - destiny
    origin_to_destiny = origin - destiny

    return (
        abs(robot_to_origin.dot_product(robot_to_destiny))
        / origin_to_destiny.distance()
    )


# def check_performace(
#     plant_grid: PlantGridType,
#     graph: List[ProcessGraphNode[ProcessGraphEdgeWithTransport]],
# ) -> float:

#     robot_Vector = get_stations_with_transport_Vectors(plant_grid)[0]

#     node_Vectors: Dict[str, Vector] = {}

#     result = 0

#     for node in graph:
#         for colIndex, column in enumerate(plant_grid):
#             for rowIndex, station in enumerate(iterable=column):
#                 if station is None:
#                     continue
#                 if station.name == node.station.name:
#                     node_Vectors[node.station.name] = Vector(colIndex, rowIndex)

#     for node in graph:
#         for edge in node.edges:
#             stations_distance = (
#                 node_Vectors[edge.node.station.name] - node_Vectors[node.station.name]
#             ).distance()
#             robot_distance_origin = (
#                 robot_Vector - node_Vectors[node.station.name]
#             ).distance()
#             robot_distance_destiny = (
#                 robot_Vector - node_Vectors[edge.node.station.name]
#             ).distance()
#             Vector_penalty = evaluate_robot_penalties(
#                 robot_Vector,
#                 node_Vectors[node.station.name],
#                 node_Vectors[edge.node.station.name],
#             )

#             result += (
#                 stations_distance
#                 + robot_distance_origin / 4
#                 + robot_distance_destiny / 4
#                 + Vector_penalty
#             )

#     return result


def check_configuration_v2(
    plant_grid: PlantGridType,
    graph: ManufacturingProcessGraph,
) -> float:

    result = 0

    graph.reset_positions()

    for colIndex, column in enumerate(plant_grid):
        for rowIndex, station in enumerate(iterable=column):
            if station is None:
                continue
            for node in graph.nodes:
                if node.station.name == station.name:
                    node.position.set(colIndex, rowIndex)

    # There are two possible ways to calculate the performance of the configuration
    # Considering that all the edges have to be used, so all the possible paths that the robots can do have to be possible, i.e. all the edges can be used and the distance between robot and all possible nodes have to be under the robot range
    # The other way is to allow to have edges out of range, but making sure that the process can still be done, i.e. the process required parts can reach the objective manufacturing process nodes, and the result parts can reach the output nodes
    # The first method is more strict, but the second one is more realistic, as usually each robot would be programed to do the paths that it is more efficient, and the paths that are less efficient would be done by other robots. Something like and specialized robot for each path, although some paths could be done by more than one robot for flexibility.

    # Anyway, the first method is more simple to implement, so we are going to use it for now

    # We are going to iterate through all the edges, check the distance between the robot and the origin, or the robot and the destiny, to check if the robot can do the path

    # Here we are going to iterate through all the edges, check the distance between the origin and the destiny and return false is any distance is bigger than the robot range
    for edge in graph.edges:
        stations_distance = (edge.origin.position - edge.destiny.position).distance()
        if edge.origin.station.transport is not None:
            if edge.origin.station.transport.range < stations_distance:
                # print("Edge out of range")
                # print("Origin station: " + edge.origin.station.name)
                # print("Destiny station: " + edge.destiny.station.name)
                # print("Stations distance: " + str(stations_distance))
                # print("Robot range: " + str(edge.origin.station.transport.range))
                # print("Robot position: " + str(edge.origin.position))
                # print("Destiny position: " + str(edge.destiny.position))

                return False
        if edge.destiny.station.transport is not None:
            if edge.destiny.station.transport.range < stations_distance:
                return False

    return True


def check_performace_v2(
    plant_grid: PlantGridType,
    graph: ManufacturingProcessGraph,
) -> float:

    result = 0

    graph.reset_positions()

    for colIndex, column in enumerate(plant_grid):
        for rowIndex, station in enumerate(iterable=column):
            if station is None:
                continue
            for node in graph.nodes:
                if node.station.name == station.name:
                    node.position.set(colIndex, rowIndex)

    # There are two possible ways to calculate the performance of the configuration
    # Considering that all the edges have to be used, so all the possible paths that the robots can do have to be possible, i.e. all the edges can be used and the distance between robot and all possible nodes have to be under the robot range
    # The other way is to allow to have edges out of range, but making sure that the process can still be done, i.e. the process required parts can reach the objective manufacturing process nodes, and the result parts can reach the output nodes
    # The first method is more strict, but the second one is more realistic, as usually each robot would be programed to do the paths that it is more efficient, and the paths that are less efficient would be done by other robots. Something like and specialized robot for each path, although some paths could be done by more than one robot for flexibility.

    # Anyway, the first method is more simple to implement, so we are going to use it for now

    # We are going to iterate through all the edges, check the distance between the robot and the origin, or the robot and the destiny, to check if the robot can do the path

    for edge in graph.edges:
        stations_distance = (edge.origin.position - edge.destiny.position).distance()
        result += stations_distance



    return result