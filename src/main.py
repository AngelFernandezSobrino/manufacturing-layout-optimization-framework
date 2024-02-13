# import library to read a yaml file

import random
from typing import Dict, List
from src.solver_graph import (
    Position,
    Node,
    add_nodes,
    check_configuration,
    check_performace,
    create_plant_from_node,
    create_plant_from_node_with_station_models_used,
    get_stations_with_transport_positions,
    get_available_positions,
)

from src.outputs import now_string

import model
from src.process_graphs_tools import export_tree_graph

station_models = model.get_stations_model()

plant_grid: model.PlantGridType = model.get_void_plant_grid()

# The position 0, 3 is the center of the first row, and has to contain the InOut station

plant_grid[0][2] = station_models.pop("InOut")

[print(model) for model in station_models.values()]

# The next step is to place one of the remaining stations in the grid, in a position that has to be nearby some of the previous stations<F

# First of all, we need to know the possible positions for the station. For we iterate over the grid and check if the position is empty and if the some position nearby is not empty


while len(station_models) > 0:
    available_positions_array: List[Position] = []
    available_positions_grid: List[List[int]] = [
        [0 for x in range(5)] for y in range(5)
    ]

    for position in available_positions_array:
        available_positions_grid[position.y][position.x] = 1

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

    model.print_table(available_positions_grid)

    print("[", end="")
    for position in available_positions_array:
        print(position, end="")
        print(", ", end="")

    print("]")

    # Now we have the available positions, we can choose one of them randomly

    # The number of available position is the length of the array available_positions_array
    # We need a random number between 0 and the length of the array - 1

    random_position_index = random.randint(0, len(available_positions_array) - 1)

    print(f"Random position index: {random_position_index}")

    # Now we have the index, we can get the position

    random_position = available_positions_array[random_position_index]

    print(f"Random position: {random_position}")

    # Now we have the position, we can choose one of the remaining stations randomly

    # The number of remaining stations is the length of the array stationModels

    random_station_index = random.randint(0, len(station_models) - 1)

    print(f"Random station index: {random_station_index}")

    # Now we have the index, we can get the station

    random_station_name = list(station_models.keys())[random_station_index]

    print(f"Random station: {random_station_name}")

    # Now we have the position and the station, we can place the station in the grid

    plant_grid[random_position.y][random_position.x] = station_models.pop(
        random_station_name
    )

    model.print_table(plant_grid)

print("Configuration obtained")

# To create all the different configurations we are going to build a tree of configurations.
# Starting from the initial conditions, with the InOut station on the top-middle position.

station_models = model.get_stations_model()


def populate_next_nodes(node: Node, remaining_stations: int):
    if remaining_stations <= 0:
        return

    global station_models

    plant_grid, station_models_used = create_plant_from_node_with_station_models_used(
        node
    )
    available_positions_array, available_positions_grid = get_available_positions(
        plant_grid
    )

    for position in available_positions_array:
        for value in station_models.values():
            if value.name in station_models_used:
                continue

            new_node = Node(value, position, node)

            if node.next_nodes is None:
                node.next_nodes = []

            node.next_nodes.append(new_node)

            populate_next_nodes(new_node, remaining_stations - 1)


first_node = Node(station_models["InOut"], Position(2, 0), None)

populate_next_nodes(first_node, len(station_models) - 1)


def fn1(number: int, length) -> int:
    return number - length / 2


export_tree_graph()


# Now we have the tree of configurations, we need to check if the configuration is valid or not
# To do that, we need to check if part1 and part2 can reach Press station from InOut station and that part3 can reach InOut station from Press station
# As the robot can move the three parts, we onli need to check if part1 can reach Press station from InOut station

# To do that we need to check if the robot can reach the desired stations.
# In that case, it is check by the distance between the stations and the range of the robot, in that case, the robot has to be next to the station to be able to reach it

# To check that, we are going to search for the robot in a given configuration and the check is the Press station and the InOut station are in the neighborhood of the robot

# To do that, we are going to create a function that returns the position of the robot in a given configuration

stationModelsOriginal = model.get_stations_model()


# Now we have the position of the robot, we can check if the Press station and the InOut station are in the neighborhood of the robot


def check_configuration_each_leave(node: Node):
    if node.next_nodes is None:
        plant_grid = create_plant_from_node(node)

        if check_configuration(plant_grid):
            print("Configuration valid")
            return True
        else:
            print("Configuration not valid")
            return False

    at_least_one_valid = False

    for index, next_node in enumerate(node.next_nodes):
        if check_configuration_each_leave(next_node):
            at_least_one_valid = True
        else:
            del node.next_nodes[index]

    return at_least_one_valid


check_configuration_each_leave(first_node)

print("Configurations checked")

# Print graph again

export_tree_graph()

# Now we need to check each configuration to evaluate the cost of the configuration

# This function will be able to get a permorfance ratio for a given configuration. Thats the bigges problem actualy.
# We will start with a simpler, easier to calculate, performance ratio. That would be improve in the future.


# graphs.nodes_v2 is a graph that contains all the storage nodes and the parts that can be transfered between them
# Now we have to evaluate each part transfer, looking for the lenght of the path and how much far away is the robot from the nodes
# With that information we can do an estimation of the time required for the path to be completed
# With al the paths evaluated, we can calculate the performance ratio
# The performance ratio would be directly proportional to the system productivity, although it is not the same,
# but it is a good ratio that we can use for the comparison of the different configurations
# The real part path time and the real performance ratio could be later calculated, but it is not the objective as this result is good enough for the comparison
# A pathfinding algorithm could be used to calculate the real path time, and then having the shorter paths available would contribute to a better performance ratio
# The only problem is the ponderation of the different paths. It is more important to have a shorter path for a transfer that is done more frequently
# than for a transfer that is done less frequently.
# Some of the paths require to be done at least once. Other paths are no required, but they could be used for the system to be more flexible.
# For example, intermediate storage places can be used as a buffer for the system, considering that the parts input ratio is not constant. In systems with
# important variations in the parts input ratio can be specially problematic.

# Considering each edge in graph.nodes_v2, we are going to iterate through all the configurations and calculate the performance ratio for each configuration


best_performance_ratio: float = 9999999999.0
best_performance_node: Node | None = None


def check_performance_each_leave(node: Node):
    if node.next_nodes is None:
        plant_grid = create_plant_from_node(node)

        plant_performace = check_performace(plant_grid)

        global best_performance_ratio
        global best_performance_node

        if plant_performace < best_performance_ratio:
            best_performance_ratio = plant_performace
            best_performance_node = node

        return

    for next_node in node.next_nodes:
        check_performance_each_leave(next_node)


check_performance_each_leave(first_node)

print("Performance checked")
print("Best performance ratio: " + str(best_performance_ratio))
print("Best performance node: " + str(best_performance_node))

if best_performance_node:
    plant_grid = create_plant_from_node(best_performance_node)

    # Print that configuration

    model.print_table(plant_grid)
