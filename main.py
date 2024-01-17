# import library to read a yaml file
from ast import Add
from asyncio import Transport
from cProfile import label
import copy
from ctypes import Array
from dataclasses import dataclass
from lib2to3.fixes import fix_set_literal
from math import cos, pi, sin
from os import name
from pickle import FALSE
import random
import stat
from tkinter import N
from typing import Any, Dict, List, TypedDict
from urllib import robotparser
from xml.etree.ElementTree import PI
from networkx import second_order_centrality
import yaml
import prettytable

model_file = open("model.yaml", "r")

model = yaml.full_load(model_file)

class TransportType(TypedDict):
    Range: int
    Parts: list[str]

class StorageType(TypedDict):
    Type: list[str]
    Place: Any
    Add: int
    Remove: int

@dataclass
class StationModel:
    name: str
    storage: list[StorageType] | None
    transport: TransportType | None
    activities: list[str] | None

    def __str__(self) -> str:
        return f"{self.name}"

stationModels: Dict[str, StationModel] = {}



for key, value in model["Stations"]["Models"].items():
    stationModels[key] = StationModel(
        key,
        value.get("Storage", None),
        value.get("Transport", None),
        value.get("Activities", None),
    )

# Make a deep copy of the stationModels dict
    
stationModelsOriginal = copy.deepcopy(stationModels)


# Model consist on stations and properties
# The first step would be to generate a 5x5 grid to place the stations


plant_grid_type = List[List[StationModel | None]]

plant_grid: plant_grid_type = [[None for x in range(5)] for y in range(5)]

# The position 0, 3 is the center of the first row, and has to contain the InOut station

plant_grid[0][2] = stationModels.pop("InOut")

# Print plant grid

def print_table(plant_grid, width=15):
    table = prettytable.PrettyTable()
    column_names = ["", "0", "1", "2", "3", "4"]
    table_width: dict[str, int] = {}

    for name in column_names:
        table_width[name] = width

    table.field_names = column_names
    table._max_width = table_width
    table._min_width = table_width

    for row_index, row in enumerate(plant_grid):
        table.add_row([row_index, *row])

    print(table)

print_table(plant_grid)


[print(model) for model in stationModels.values()]

# The next step is to place one of the remaining stations in the grid, in a position that has to be nearby some of the previous stations<F

# First of all, we need to know the possible positions for the station. For we iterate over the grid and check if the position is empty and if the some position nearby is not empty


@dataclass
class Position:
    x: int
    y: int

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"


while len(stationModels) > 0:

    available_positions_array: List[Position] = []
    available_positions_grid: List[List[int]] = [[0 for x in range(5)] for y in range(5)]

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


    print_table(available_positions_grid)

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

    random_station_index = random.randint(0, len(stationModels) - 1)

    print(f"Random station index: {random_station_index}")

    # Now we have the index, we can get the station

    random_station_name = list(stationModels.keys())[random_station_index]

    print(f"Random station: {random_station_name}")

    # Now we have the position and the station, we can place the station in the grid

    plant_grid[random_position.y][random_position.x] = stationModels.pop(random_station_name)

    print_table(plant_grid)

print("Configuration obtained")

def test(plant_grid: List[List[StationModel | None]]):

    available_positions_array: List[Position] = []
    available_positions_grid: List[List[int]] = [[0 for x in range(5)] for y in range(5)]

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

# To create all the different configurations we are going to build a tree of configurations.
# Starting from the initial conditions, with the InOut station on the top-middle position.

stationModels_2 = copy.deepcopy(stationModelsOriginal)

class Node():
    def __init__(self, station: StationModel, position: Position) -> None:
        self.station: StationModel = station
        self.position: Position = position

    def __str__(self) -> str:
        return f"{self.station} {self.position}"

first_level: Node = Node(stationModels_2.pop("InOut"), Position(2, 0))

plant_grid = [[None for x in range(5)] for y in range(5)]

plant_grid[first_level.position.y][first_level.position.x] = first_level.station

second_level: List[Node] = []

available_positions_array, available_positions_grid = test(plant_grid)

for position in available_positions_array:
    for value in stationModels_2.values():
        second_level.append(Node(value, position))


third_level: List[List[Node]] = []

for perIndex, permutation in enumerate(second_level):

    third_level.append([])

    stationModels_3 = copy.deepcopy(stationModelsOriginal)

    plant_grid = [[None for x in range(5)] for y in range(5)]

    plant_grid[first_level.position.y][first_level.position.x] = first_level.station

    stationModels_3.pop(first_level.station.name)

    plant_grid[permutation.position.y][permutation.position.x] = permutation.station
    stationModels_3.pop(permutation.station.name)

    available_positions_array, available_positions_grid = test(plant_grid)

    for position in available_positions_array:
        for value in stationModels_3.values():
            third_level[perIndex].append(Node(value, position))

fourth_level: List[List[List[Node]]] = []

for perIndex, permutation in enumerate(second_level):
    fourth_level.append([])
    for perIndex2, permutation2 in enumerate(third_level[perIndex]):

        fourth_level[perIndex].append([])

        stationModels_4 = copy.deepcopy(stationModelsOriginal)

        plant_grid = [[None for x in range(5)] for y in range(5)]

        plant_grid[first_level.position.y][first_level.position.x] = first_level.station

        stationModels_4.pop(first_level.station.name)

        plant_grid[permutation.position.y][permutation.position.x] = permutation.station
        stationModels_4.pop(permutation.station.name)

        plant_grid[permutation2.position.y][permutation2.position.x] = permutation2.station
        stationModels_4.pop(permutation2.station.name)

        available_positions_array, available_positions_grid = test(plant_grid)

        for position in available_positions_array:
            for value in stationModels_4.values():
                fourth_level[perIndex][perIndex2].append(Node(value, position))

fifth_level: List[List[List[List[Node]]]] = []

for perIndex, permutation in enumerate(second_level):
    fifth_level.append([])
    for perIndex2, permutation2 in enumerate(third_level[perIndex]):
        fifth_level[perIndex].append([])
        for perIndex3, permutation3 in enumerate(fourth_level[perIndex][perIndex2]):

            fifth_level[perIndex][perIndex2].append([])

            stationModels_5 = copy.deepcopy(stationModelsOriginal)

            plant_grid = [[None for x in range(5)] for y in range(5)]

            plant_grid[first_level.position.y][first_level.position.x] = first_level.station

            stationModels_5.pop(first_level.station.name)

            plant_grid[permutation.position.y][permutation.position.x] = permutation.station
            stationModels_5.pop(permutation.station.name)

            plant_grid[permutation2.position.y][permutation2.position.x] = permutation2.station
            stationModels_5.pop(permutation2.station.name)

            plant_grid[permutation3.position.y][permutation3.position.x] = permutation3.station
            stationModels_5.pop(permutation3.station.name)

            available_positions_array, available_positions_grid = test(plant_grid)

            for position in available_positions_array:
                for value in stationModels_5.values():
                    fifth_level[perIndex][perIndex2][perIndex3].append(Node(value, position))


def fn1(number: int, length) -> int:
    return number - length/2

import pyvis as vis # type: ignore
import networkx as nx # type: ignore

graph_viewer = vis.network.Network(height="1000px")
graph_generator = nx.Graph()

graph_generator.add_node(first_level.station.name + str(first_level.position), label=(first_level.station.name + str(first_level.position)), physics=False, x=0, y=0)

for index2, node in enumerate(second_level):
    x = fn1(index2, len(second_level)) * 120
    graph_generator.add_node(f"2:{index2}:{node.station.name}:{node.position}", label=f"2:{index2}:{node.station.name}:{node.position}", physics=False, x=x, y=60)
    graph_generator.add_edge(first_level.station.name + str(first_level.position), f"2:{index2}:{node.station.name}:{node.position}")

for index2, nodes in enumerate(third_level):
    for index3, node in enumerate(nodes):
        x = fn1(index3, len(nodes)) * 120 - 800 + 250*index2
        graph_generator.add_node(f"3:{index2}:{index3}:{node.station.name}:{node.position}", label=f"3:{index2}:{index3}:{node.station.name}:{node.position}", physics=False, x=x, y=120+60*index2)
        graph_generator.add_edge(f"2:{index2}:{second_level[index2].station.name}:{second_level[index2].position}", f"3:{index2}:{index3}:{node.station.name}:{node.position}")

for index2, nodes1 in enumerate(fourth_level):
    for index3, nodes in enumerate(nodes1):
        for index4, node in enumerate(nodes):
            x = fn1(index4, len(nodes)) * 120 - 800 + 250*index3 - 2000 + 500*index2
            graph_generator.add_node(f"4:{index2}:{index3}:{index4}:{node.station.name}:{node.position}", label=f"4:{index2}:{index3}:{index4}:{node.station.name}:{node.position}", physics=False, x=x, y=120+60*index2 + 400 + 60*index3)
            graph_generator.add_edge(f"3:{index2}:{index3}:{third_level[index2][index3].station.name}:{third_level[index2][index3].position}", f"4:{index2}:{index3}:{index4}:{node.station.name}:{node.position}")


# graph_viewer.toggle_physics(False)
graph_viewer.from_nx(graph_generator)
graph_viewer.barnes_hut(gravity=0, central_gravity=0.3, spring_length=100, damping=0.09, overlap=0.1)
# graph_viewer.set_edge_smooth('dynamic')
graph_viewer.save_graph("tree.html")


# Now we have the tree of configurations, we need to check if the configuration is valid or not
# To do that, we need to check if part1 and part2 can reach Press station from InOut station and that part3 can reach InOut station from Press station
# As the robot can move the three parts, we onli need to check if part1 can reach Press station from InOut station

# To do that we need to check if the robot can reach the desired stations.
# In that case, it is check by the distance between the stations and the range of the robot, in that case, the robot has to be next to the station to be able to reach it

# To check that, we are going to search for the robot in a given configuration and the check is the Press station and the InOut station are in the neighborhood of the robot

# To do that, we are going to create a function that returns the position of the robot in a given configuration

def get_robot_position(plant_grid: List[List[StationModel | None]]) -> Position:

    for y in range(5):
        for x in range(5):
            if plant_grid[y][x] == stationModelsOriginal["Robot"]:
                return Position(x, y)

    raise Exception("Robot not found")

# Now we have the position of the robot, we can check if the Press station and the InOut station are in the neighborhood of the robot

def check_configuration(plant_grid: List[List[StationModel | None]]) -> bool:

    robot_position = get_robot_position(plant_grid)

    if (robot_position.x > 0 and plant_grid[robot_position.y][robot_position.x - 1] == stationModelsOriginal["Press"]) or \
        (robot_position.x < 4 and plant_grid[robot_position.y][robot_position.x + 1] == stationModelsOriginal["Press"]) or \
        (robot_position.y > 0 and plant_grid[robot_position.y - 1][robot_position.x] == stationModelsOriginal["Press"]) or \
        (robot_position.y < 4 and plant_grid[robot_position.y + 1][robot_position.x] == stationModelsOriginal["Press"] or \
        (robot_position.x > 0 and robot_position.y > 0 and plant_grid[robot_position.y - 1][robot_position.x - 1] == stationModelsOriginal["Press"]) or \
        (robot_position.x < 4 and robot_position.y > 0 and plant_grid[robot_position.y - 1][robot_position.x + 1] == stationModelsOriginal["Press"]) or \
        (robot_position.x > 0 and robot_position.y < 4 and plant_grid[robot_position.y + 1][robot_position.x - 1] == stationModelsOriginal["Press"]) or \
        (robot_position.x < 4 and robot_position.y < 4 and plant_grid[robot_position.y + 1][robot_position.x + 1] == stationModelsOriginal["Press"])):
            if (robot_position.x > 0 and plant_grid[robot_position.y][robot_position.x - 1] == stationModelsOriginal["InOut"]) or \
                (robot_position.x < 4 and plant_grid[robot_position.y][robot_position.x + 1] == stationModelsOriginal["InOut"]) or \
                (robot_position.y > 0 and plant_grid[robot_position.y - 1][robot_position.x] == stationModelsOriginal["InOut"]) or \
                (robot_position.y < 4 and plant_grid[robot_position.y + 1][robot_position.x] == stationModelsOriginal["InOut"] or \
                (robot_position.x > 0 and robot_position.y > 0 and plant_grid[robot_position.y - 1][robot_position.x - 1] == stationModelsOriginal["InOut"]) or \
                (robot_position.x < 4 and robot_position.y > 0 and plant_grid[robot_position.y - 1][robot_position.x + 1] == stationModelsOriginal["InOut"]) or \
                (robot_position.x > 0 and robot_position.y < 4 and plant_grid[robot_position.y + 1][robot_position.x - 1] == stationModelsOriginal["InOut"]) or \
                (robot_position.x < 4 and robot_position.y < 4 and plant_grid[robot_position.y + 1][robot_position.x + 1] == stationModelsOriginal["InOut"])):
                    return True
            else:
                return False
    else:   
        return False
    

# Now we have the function to check if a configuration is valid or not, we can check all the configurations
    
for perIndex, permutation in enumerate(second_level):
    for perIndex2, permutation2 in enumerate(third_level[perIndex]):
        for perIndex3, permutation3 in enumerate(fourth_level[perIndex][perIndex2]):

            stationModels_5 = copy.deepcopy(stationModelsOriginal)

            plant_grid = [[None for x in range(5)] for y in range(5)]

            plant_grid[first_level.position.y][first_level.position.x] = first_level.station

            stationModels_5.pop(first_level.station.name)

            plant_grid[permutation.position.y][permutation.position.x] = permutation.station
            stationModels_5.pop(permutation.station.name)

            plant_grid[permutation2.position.y][permutation2.position.x] = permutation2.station
            stationModels_5.pop(permutation2.station.name)

            plant_grid[permutation3.position.y][permutation3.position.x] = permutation3.station
            stationModels_5.pop(permutation3.station.name)

            if check_configuration(plant_grid):
                print("Configuration valid")
            else:
                print("Configuration not valid")
                # Delete the configuration
                del fourth_level[perIndex][perIndex2][perIndex3]

        if len(fourth_level[perIndex][perIndex2]) == 0:
            del third_level[perIndex][perIndex2]
    if len(third_level[perIndex]) == 0:
        del second_level[perIndex]

print("Configurations checked")

# Print graph again


graph_viewer_2 = vis.network.Network(height="1000px")
graph_generator_2 = nx.Graph()

graph_generator_2.add_node(first_level.station.name + str(first_level.position), label=(first_level.station.name + str(first_level.position)), physics=False, x=0, y=0)

for index2, node in enumerate(second_level):
    x = fn1(index2, len(second_level)) * 120
    graph_generator_2.add_node(f"2:{index2}:{node.station.name}:{node.position}", label=f"2:{index2}:{node.station.name}:{node.position}", physics=False, x=x, y=60)
    graph_generator_2.add_edge(first_level.station.name + str(first_level.position), f"2:{index2}:{node.station.name}:{node.position}")

for index2, nodes in enumerate(third_level):
    for index3, node in enumerate(nodes):
        x = fn1(index3, len(nodes)) * 120 - 800 + 250*index2
        graph_generator_2.add_node(f"3:{index2}:{index3}:{node.station.name}:{node.position}", label=f"3:{index2}:{index3}:{node.station.name}:{node.position}", physics=False, x=x, y=120+60*index2)
        graph_generator_2.add_edge(f"2:{index2}:{second_level[index2].station.name}:{second_level[index2].position}", f"3:{index2}:{index3}:{node.station.name}:{node.position}")

for index2, nodes1 in enumerate(fourth_level):
    for index3, nodes in enumerate(nodes1):
        for index4, node in enumerate(nodes):
            x = fn1(index4, len(nodes)) * 120 - 800 + 250*index3 - 2000 + 500*index2
            graph_generator_2.add_node(f"4:{index2}:{index3}:{index4}:{node.station.name}:{node.position}", label=f"4:{index2}:{index3}:{index4}:{node.station.name}:{node.position}", physics=False, x=x, y=120+60*index2 + 400 + 60*index3)
            graph_generator_2.add_edge(f"3:{index2}:{index3}:{third_level[index2][index3].station.name}:{third_level[index2][index3].position}", f"4:{index2}:{index3}:{index4}:{node.station.name}:{node.position}")


graph_viewer_2.from_nx(graph_generator_2)
graph_viewer_2.barnes_hut(gravity=0, central_gravity=0.3, spring_length=100, damping=0.09, overlap=0.1)
graph_viewer_2.save_graph("tree_filtered.html")

# Now we need to check each configuration to evaluate the cost of the configuration
