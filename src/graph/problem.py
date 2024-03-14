from __future__ import annotations
from dataclasses import dataclass
import itertools
from math import sqrt
import re
from turtle import distance, st
from typing import Dict, List, Set

from graph.process import ManufacturingProcessGraph
from model import Plant, tools

from . import (
    TreeNode,
    StationNode,
    RoutingGraphEdge,
)

from model import Vector, Plant, StationModel


def create_plant_from_node_with_station_models_used(node: TreeNode):
    plant = Plant()
    station_models_used = set()
    node_evaluated = node
    while True:
        plant.grid[node_evaluated.position.y][
            node_evaluated.position.x
        ] = node_evaluated.station

        station_models_used.add(node_evaluated.station.name)

        if node_evaluated.previous is None:
            break

        node_evaluated = node_evaluated.previous

    return plant, station_models_used


def get_available_positions(
    plant: Plant,
) -> tuple[List[Vector], List[List[int]]]:
    available_Vectors_array: List[Vector] = []
    available_Vectors_grid: List[List[int]] = [[0 for x in range(5)] for y in range(5)]

    for y in range(1, 5):
        for x in range(5):
            if plant.grid[y][x] is None:
                if (
                    (plant.grid[y - 1][x] is not None)
                    or (x > 0 and plant.grid[y][x - 1] is not None)
                    or (x < 4 and plant.grid[y][x + 1] is not None)
                    or (y < 4 and plant.grid[y + 1][x] is not None)
                    or (x > 0 and plant.grid[y - 1][x - 1] is not None)
                    or (x < 4 and plant.grid[y - 1][x + 1] is not None)
                    or (y < 4 and x > 0 and plant.grid[y + 1][x - 1] is not None)
                    or (y < 4 and x < 4 and plant.grid[y + 1][x + 1] is not None)
                ):
                    available_Vectors_grid[y][x] = 1
                    available_Vectors_array.append(Vector(x, y))

    return available_Vectors_array, available_Vectors_grid


def get_stations_with_transport_vectors(
    plant: Plant,
) -> List[Vector]:

    transport_vectors: List[Vector] = []

    for y in range(5):
        for x in range(5):
            station = plant.grid[y][x]
            if station is None:
                continue
            if station.transports is not None:
                transport_vectors.append(Vector(x, y))

    if len(transport_vectors) > 0:
        return transport_vectors

    raise Exception("Robot not found")


# Now we have the function to check if a configuration is valid or not, we can check all the configurations


def evaluate_robot_penalties(robot: Vector, origin: Vector, destiny: Vector):
    robot_to_origin = robot - origin
    robot_to_destiny = robot - destiny
    origin_to_destiny = origin - destiny

    return (
        abs(robot_to_origin.dot_product(robot_to_destiny))
        / origin_to_destiny.distance()
    )


def check_configuration_v2(
    plant: Plant,
    graph: ManufacturingProcessGraph,
) -> float:

    result = 0

    graph.reset_positions()

    for colIndex, column in enumerate(plant.grid):
        for rowIndex, station in enumerate(iterable=column):
            if station is None:
                continue
            for node in graph.station_nodes:
                if node.model.name == station.name:
                    node.position.set(colIndex, rowIndex)
    """
    There are two possible ways to calculate the performance of the configuration
    Considering that all the edges have to be used, so all the possible paths that the robots can do have to be possible, i.e. all the edges can be used and the distance between robot and all possible nodes have to be under the robot range
    The other way is to allow to have edges out of range, but making sure that the process can still be done, i.e. the process required parts can reach the objective manufacturing process nodes, and the result parts can reach the output nodes
    The first method is more strict, but the second one is more realistic, as usually each robot would be programed to do the paths that it is more efficient, and the paths that are less efficient would be done by other robots. Something like and specialized robot for each path, although some paths could be done by more than one robot for flexibility.

    Anyway, the first method is more simple to implement, so we are going to use it for now

    We are going to iterate through all the edges, check the distance between the robot and the origin, or the robot and the destiny, to check if the robot can do the path

    Here we are going to iterate through all the edges, check the distance between the origin and the destiny and return false is any distance is bigger than the robot range
    """
    for edge in graph.routing_edges:

        stations_distance = (
            edge.transport.position - edge.storage.absolute_position()
        ).distance()

        stations_distance = (
            plant.get_shortest_path_lenght_between_two_points_using_transport()
        )

        if edge.transport.model.transports.range < stations_distance:  # type: ignore
            return False

    return True


def check_performace_v2(
    plant: Plant,
    graph: ManufacturingProcessGraph,
) -> float:

    result = 0

    graph.reset_positions()

    for colIndex, column in enumerate(plant.grid):
        for rowIndex, station in enumerate(iterable=column):
            if station is None:
                continue
            for node in graph.station_nodes:
                if node.model.name == station.name:
                    node.position.set(colIndex, rowIndex)
    """
    There are two possible ways to calculate the performance of the configuration
    Considering that all the edges have to be used, so all the possible paths that the robots can do have to be possible, i.e. all the edges can be used and the distance between robot and all possible nodes have to be under the robot range
    The other way is to allow to have edges out of range, but making sure that the process can still be done, i.e. the process required parts can reach the objective manufacturing process nodes, and the result parts can reach the output nodes
    The first method is more strict, but the second one is more realistic, as usually each robot would be programed to do the paths that it is more efficient, and the paths that are less efficient would be done by other robots. Something like and specialized robot for each path, although some paths could be done by more than one robot for flexibility.

    Anyway, the first method is more simple to implement, so we are going to use it for now

    We are going to iterate through all the edges, check the distance between the robot and the origin, or the robot and the destiny, to check if the robot can do the path
    """
    for edge in graph.pathing_edges:
        stations_distance = (
            edge.origin.absolute_position() - edge.destiny.absolute_position()
        ).distance()
        result += stations_distance

    return result


"""
Function to build a visibility graph, with the nodes of all the corners of the obstacles of the plant 

The visibility graph contains all the possible paths between the nodes, and the distance between the nodes

Then, this visibility graph has to be adapted to each transport station. From the center of the transport station, only the nodes that are visible from the center of the transport station are going to be considered for the pathfinding algorithm

"""


class VisibilityGraphSelfImplemented:
    def __init__(self, plant: Plant):
        self.nodes: List[VisibilityGraphNode] = []
        self.edges: List[VisibilityGraphEdge] = []
        self.plant = plant

    def build(self):
        for y in range(5):
            for x in range(5):
                station = self.plant.grid[y][x]
                if station is None:
                    continue
                self.get_vectors_from_station(station, Vector(float(x), float(y)))

    def get_vectors_from_station(self, station: StationModel, position: Vector[float]):
        if station.obstacles is None:
            return
        for obstacle in station.obstacles:
            north = VisibilityGraphNode(
                float(obstacle.center.x + obstacle.size.x / 2),
                float(obstacle.center.y + obstacle.size.y / 2),
            )
            south = VisibilityGraphNode(
                float(obstacle.center.x - obstacle.size.x / 2),
                float(obstacle.center.y - obstacle.size.y / 2),
            )
            east = VisibilityGraphNode(
                float(obstacle.center.x + obstacle.size.x / 2),
                float(obstacle.center.y - obstacle.size.y / 2),
            )
            west = VisibilityGraphNode(
                float(obstacle.center.x - obstacle.size.x / 2),
                float(obstacle.center.y + obstacle.size.y / 2),
            )

            nodes_list = [north, south, east, west]

            for combination in itertools.permutations(nodes_list, 4):
                if intersect(
                    combination[0].position,
                    combination[1].position,
                    combination[2].position,
                    combination[3].position,
                ):
                    continue
                edges_list = [
                    VisibilityGraphEdge(combination[0], combination[1]),
                    VisibilityGraphEdge(combination[2], combination[3]),
                ]

                for edge in edges_list:
                    if edge not in self.edges:
                        self.edges.append(edge)

            self.nodes.extend(nodes_list)


class VisibilityGraphNode:
    def __init__(self, x: float, y: float):
        self.position = Vector(x, y)
        self.edges: List[VisibilityGraphEdge]


class VisibilityGraphEdge:
    def __init__(self, A: VisibilityGraphNode, B: VisibilityGraphNode):
        self.nodes = (A, B)
        self.distance = (A.position - B.position).distance()

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, VisibilityGraphEdge):
            return False
        return (
            self.nodes[0] == __value.nodes[0] and self.nodes[1] == __value.nodes[1]
        ) or (self.nodes[0] == __value.nodes[1] and self.nodes[1] == __value.nodes[0])


def ccw(A: Vector[float], B: Vector[float], C: Vector[float]):
    return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)


def intersect(A: Vector[float], B: Vector[float], C: Vector[float], D: Vector[float]):
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)
