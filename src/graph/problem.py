from __future__ import annotations
import itertools

from graph.process import ManufacturingProcessGraph
from model import tools
from model.plant import Plant, path_distance

from . import (
    TreeNode,
)

from model import Vector


def get_hash_for_new_node(node: TreeNode, previous_node: TreeNode):
    previous_node_evaluated = previous_node
    hash_set: set[str] = set()

    hash_set.add(node.station.name + str(node.position))

    while True:
        hash_set.add(
            previous_node_evaluated.station.name + str(previous_node_evaluated.position)
        )
        if previous_node_evaluated.previous is None:
            break
        previous_node_evaluated = previous_node_evaluated.previous

    return hash_set


def create_plant_from_node_with_station_models_used(
    node: TreeNode, system_specification: tools.SystemSpecification
) -> tuple[Plant, set[str]]:
    grid = system_specification.model.stations.grid
    plant = Plant(system_specification.model.stations.grid)
    station_models_used: set[str] = set()
    node_evaluated = node
    while True:

        plant.set_location(node_evaluated.position, node_evaluated.station)

        station_models_used.add(node_evaluated.station.name)

        if node_evaluated.previous is None:
            break

        node_evaluated = node_evaluated.previous

    plant.ready()

    return plant, station_models_used


def get_available_positions(plant: Plant) -> list[Vector[int]]:

    available_positions: list[Vector] = []

    for x, y in itertools.product(
        range(plant.grid_params.size.x), range(1, plant.grid_params.size.y)
    ):
        if plant.grid[y][x] is None:
            if (
                (y > 0 and plant.grid[y - 1][x] is not None)
                or (x > 0 and plant.grid[y][x - 1] is not None)
                or (x < 4 and plant.grid[y][x + 1] is not None)
                or (y < 4 and plant.grid[y + 1][x] is not None)
            ):
                available_positions.append(Vector(x, y))

    return available_positions


def get_stations_with_transport_vectors(
    plant: Plant,
) -> list[Vector]:

    transport_vectors: list[Vector] = []

    for x, y in itertools.product(
        range(plant.grid_params.size.x), range(plant.grid_params.size.y)
    ):
        station = plant.get_location_coordinates(x, y)
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

    plant.build_vis_graphs()
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

        stations_distance = path_distance(
            plant.get_path_between_two_points_with_transport(
                edge.transport.position,
                edge.storage.absolute_position(),
                edge.transport.model.name,
            )
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


def evaluate_plant(
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
