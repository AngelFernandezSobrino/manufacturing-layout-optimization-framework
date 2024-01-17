# import library to read a yaml file
from ast import Add
from asyncio import Transport
from cProfile import label
import copy
from ctypes import Array
from dataclasses import dataclass
from math import cos, pi, sin
from os import name
from pickle import FALSE
import random
import stat
from typing import Any, Dict, List, TypedDict
from xml.etree.ElementTree import PI
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


# Now we are going to generate a graph with all the posible part flows in the plant
# For doing that, first we need to know the objective of the process
# In this case, the objective is to produce the part 3

objectives = model['Process']['Objectives'] # This is a list of parts, in the test case, ["Part3"]

# We have also available the list of activities that produce each part in the model, we are going to asume that the only part is part 3

activities_producing_part_3 = model['Process']['Part3'] # This is a list of activities objects, in the test case, [Activity1]

# Now we need to identify the stations that produce the parts in the objectives list

stations_producing_objectives = []

for station in stationModelsOriginal.values():
    if station.activities is not None:
        for activity in station.activities:
            for activity_producing_part_3 in activities_producing_part_3:
                if activity in list(activity_producing_part_3.keys()):
                    stations_producing_objectives.append(station)

print("Stations producing objectives:")
[print(station) for station in stations_producing_objectives]

# Now we are going to build a graph with all the possible part flows
# It has to represent the possible part flows between the stations

# We need a class to represent the edges of the graph, it would contain the part and the destination node

@dataclass
class Edge:
    part: str
    destination: Any

    def __str__(self) -> str:
        return f"Part: {self.part}, Destination: {self.destination}"
    
    def __eq__(self, __value) -> bool:
        if self.part == __value.part and self.destination == __value.destination:
            return True
        else:
            return False

# We need a class to represent the each node of the graph, it would contain the station and all the directed edges to the other stations
# Edges may have a part associated

@dataclass
class Node:
    station: StationModel
    outgoing_edges: List[Any]

    def __str__(self) -> str:
        return f"Station: {self.station}"
    

# First we are going to define a node for each station in the plant
    
nodes: List[Node] = []

for station in stationModelsOriginal.values():
    nodes.append(Node(station, []))

print("Nodes:")
[print(node) for node in nodes]

# Now we are going to add edges to the nodes
# All edges are going from/to a transport station to/from a storage station
# We are going to iterate over the nodes and add the edges to all the other nodes available

def circunstripted_penthagon_coordinates_gen(h, k, r, theta):
    i = 0
    while(i < 5):
        theta = 2*pi/5
        x = h + r*cos(theta + i*(2*pi/5))
        y = k + r*sin(theta + i*(2*pi/5))
        yield (x, y)
        i += 1

for node in nodes:

    node.outgoing_edges = []

    for other_node in nodes:
        if node.station.transport is not None and other_node.station.storage is not None and \
            node.station.name != other_node.station.name:
                
                for part in node.station.transport["Parts"]:
                    for storage_slot in other_node.station.storage:
                        if part in storage_slot["Type"] and storage_slot["Add"] == 1:
                            new_edge = Edge(part, other_node)
                            if new_edge not in node.outgoing_edges:
                                node.outgoing_edges.append(new_edge)

        if node.station.storage is not None and other_node.station.transport is not None and \
            node.station.name != other_node.station.name:
                
                for part in other_node.station.transport["Parts"]:
                    for storage_slot in node.station.storage:
                        if part in storage_slot["Type"] and storage_slot["Remove"] == 1:
                            new_edge = Edge(part, other_node)
                            if new_edge not in node.outgoing_edges:
                                node.outgoing_edges.append(new_edge)


nodes_table = prettytable.PrettyTable()

nodes_table.field_names = ["Node", "Outgoing edges"]



for node in nodes:
    for edge in node.outgoing_edges:
        nodes_table.add_row([str(node), str(edge)])

print(nodes_table)

import pyvis as vis # type: ignore
import networkx as nx # type: ignore

graph_viewer = vis.network.Network(directed=True, height="1000px")
graph_generator = nx.MultiDiGraph()

coordinates_generator = circunstripted_penthagon_coordinates_gen(0, 0, 300, 0)

for node in nodes:
    coordinates = next(coordinates_generator)
    graph_generator.add_node(str(node.station.name), label=str(node.station.name), physics=False, x=coordinates[0], y=coordinates[1], size=40)

for node in nodes:
    for edge in node.outgoing_edges:
        graph_generator.add_edge(str(node.station.name), str(edge.destination.station.name), label=edge.part)

# graph_viewer.toggle_physics(False)
graph_viewer.from_nx(graph_generator)
graph_viewer.barnes_hut(gravity=-2000, central_gravity=0.3, spring_length=100, damping=0.09, overlap=0.1)
# graph_viewer.set_edge_smooth('dynamic')
graph_viewer.save_graph("graph.html")


# El siguiente paso seria modelar los tiempos de transporte entre las estaciones en funcion de la distancia entre ellas

# Vamos a probar con otra version, en este caso en el grafo solo hay nodos de almacenamiento, y las aristas son el transporte(TODO: Translate to english, sorry xd, I mixed the languages)

# We need a class to represent the edges of the graph, it would contain the part, the destination node and the transport station used

@dataclass
class EdgeWithTransport:
    part: str
    destination: Any
    transport_station: Any

    def __str__(self) -> str:
        return f"Part: {self.part}, Destination: {self.destination}, Transport station: {self.transport_station}"
    
    def __eq__(self, __value) -> bool:
        if self.part == __value.part and self.destination == __value.destination and self.transport_station == __value.transport_station:
            return True
        else:
            return False

# First we should generate a dict with all the parts in the model and the transport stations that can transport them

parts_transport_stations: Dict[str, List[StationModel]] = {}

for station in stationModelsOriginal.values():
    if station.transport is not None:
        for part in station.transport["Parts"]:
            if part not in parts_transport_stations:
                parts_transport_stations[part] = []
            parts_transport_stations[part].append(station)

# We are going to define a node for each station in the plant

nodes_v2: List[Node] = []

for station in stationModelsOriginal.values():
    if node.station.storage is not None:
        nodes_v2.append(Node(station, []))

# Now we are going to add edges to the nodes_v2
# All edges are going from/to a transport station to/from a storage station
# We are going to iterate over the nodes_v2 and add the edges to all the other nodes_v2 available

for node in nodes_v2:

    node.outgoing_edges = []

    for other_node in nodes_v2:
        if node.station.name == other_node.station.name or node.station.storage is None:
            continue
        for storage_slot in node.station.storage:
            if storage_slot["Remove"] != 1:
                continue
            for part in storage_slot["Type"]:
                if other_node.station.storage is None:
                    continue
                for other_storage_slot in other_node.station.storage:
                    if other_storage_slot["Add"] != 1:
                        continue
                    for other_part in other_storage_slot["Type"]:
                        if part != other_part:
                            continue
                        for transport_station in parts_transport_stations[part]:
                            new_edge = EdgeWithTransport(part, other_node, transport_station)
                            if new_edge in node.outgoing_edges:
                                continue
                            node.outgoing_edges.append(new_edge)

nodes_v2_table = prettytable.PrettyTable()

nodes_v2_table.field_names = ["Node", "Outgoing edges"]



for node in nodes_v2:
    for edge in node.outgoing_edges:
        nodes_v2_table.add_row([str(node), str(edge)])

print(nodes_v2_table)

import pyvis as vis
import networkx as nx

graph_viewer = vis.network.Network(directed=True, height="1000px")
graph_generator = nx.MultiDiGraph()

coordinates_generator = circunstripted_penthagon_coordinates_gen(0, 0, 300, 0)

for node in nodes_v2:
    coordinates = next(coordinates_generator)
    graph_generator.add_node(str(node.station.name), label=str(node.station.name), physics=False, x=coordinates[0], y=coordinates[1], size=40)

for node in nodes_v2:
    for edge in node.outgoing_edges:
        graph_generator.add_edge(str(node.station.name), str(edge.destination.station.name), label=str(f"{edge.part}: {edge.transport_station.name}"))

# graph_viewer.toggle_physics(False)
graph_viewer.from_nx(graph_generator)
graph_viewer.barnes_hut(gravity=-2000, central_gravity=0.3, spring_length=100, damping=0.09, overlap=0.1)
# graph_viewer.set_edge_smooth('dynamic')
graph_viewer.save_graph("graph_v2.html")


# The time of transport between the stations is going to be stimated with the distance between them, the mean speed of the transport stations and the distance between the transport stations and the storage stations

# Its also particularly important to define the process time of the press activity and the 


