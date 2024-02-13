# import library to read a yaml file
from typing import Dict, List

import src.model as model
from src.outputs import export_process_graph, print_nodes_table
import src.process_graphs_tools as process_graphs_tools


def get_model_graph():
    station_models = model.get_stations_model()
    system_model = model.get_system_model()

    # Now we are going to generate a graph with all the posible part flows in the plant
    # For doing that, first we need to know the objective of the process
    # In this case, the objective is to produce the part 3

    # We have also available the list of activities that produce each part in the model, we are going to asume that the only part is part 3

    parts_to_be_produced = system_model["Process"].keys()

    activities_to_be_executed = []

    for part_name in parts_to_be_produced:
        activities_to_be_executed += system_model["Process"][part_name]

    print("Parts to be produced:")
    [print(part) for part in parts_to_be_produced]

    print("Activities to be executed:")
    [print(activity) for activity in activities_to_be_executed]

    stations_producing_objectives = []

    for station in station_models.values():
        if station.activities is None:
            continue

        for activity in station.activities:
            if activity in activities_to_be_executed:
                stations_producing_objectives.append(station)

    print("Stations producing objectives:")
    [print(station) for station in stations_producing_objectives]

    # Now we are going to build a graph with all the possible part flows
    # It has to represent the possible part flows between the stations

    # First we are going to define a node for each station in the plant

    nodes: List[process_graphs_tools.StationNode] = []

    for station in station_models.values():
        nodes.append(process_graphs_tools.StationNode(station, []))

    print("Nodes:")
    [print(node) for node in nodes]

    # Now we are going to add edges to the nodes
    # All edges are going from/to a transport station to/from a storage station
    # We are going to iterate over the nodes and add the edges to all the other nodes available

    for node in nodes:
        node.outgoing_edges = []

        for other_node in nodes:
            if (
                node.station.transport is not None
                and other_node.station.storage is not None
                and node.station.name != other_node.station.name
            ):
                for part in node.station.transport["Parts"]:
                    for storage_slot in other_node.station.storage:
                        if part in storage_slot["Type"] and storage_slot["Add"] == 1:
                            new_edge = process_graphs_tools.Edge(part, other_node)
                            if new_edge in node.outgoing_edges:
                                continue

                            node.outgoing_edges.append(new_edge)

            if (
                node.station.storage is not None
                and other_node.station.transport is not None
                and node.station.name != other_node.station.name
            ):
                for part in other_node.station.transport["Parts"]:
                    for storage_slot in node.station.storage:
                        if part in storage_slot["Type"] and storage_slot["Remove"] == 1:
                            new_edge = process_graphs_tools.Edge(part, other_node)
                            if new_edge in node.outgoing_edges:
                                continue
                            node.outgoing_edges.append(new_edge)

    print_nodes_table(nodes)

    export_process_graph(nodes, "graph", lambda edge: edge.part)


def get_model_graph_v2():

    # Vamos a probar con otra version, en este caso en el grafo solo hay nodos de almacenamiento, y las aristas son el transporte(TODO: Translate to english, sorry xd, I mixed the languages)

    # We need a class to represent the edges of the graph, it would contain the part, the destination node and the transport station used

    # First we should generate a dict with all the parts in the model and the transport stations that<z can transport them

    station_models = model.get_stations_model()
    system_model = model.get_system_model()

    parts_transport_stations: Dict[str, List[model.StationModel]] = {}

    for station in station_models.values():
        if station.transport is not None:
            for part in station.transport["Parts"]:
                if part not in parts_transport_stations:
                    parts_transport_stations[part] = []
                parts_transport_stations[part].append(station)

    # We are going to define a node for each station in the plant

    nodes_v2: List[process_graphs_tools.StationNode] = []

    for station in station_models.values():
        if station.storage is not None:
            nodes_v2.append(process_graphs_tools.StationNode(station, []))

    # Now we are going to add edges to the nodes_v2
    # All edges are going from/to a transport station to/from a storage station
    # We are going to iterate over the nodes_v2 and add the edges to all the other nodes_v2 available

    for node in nodes_v2:
        node.outgoing_edges = []

        for other_node in nodes_v2:
            if (
                node.station.name == other_node.station.name
                or node.station.storage is None
            ):
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
                                new_edge_with_transport = (
                                    process_graphs_tools.EdgeWithTransport(
                                        part, other_node, transport_station
                                    )
                                )
                                if new_edge_with_transport in node.outgoing_edges:
                                    continue
                                node.outgoing_edges.append(new_edge_with_transport)

    print_nodes_table(nodes_v2)

    export_process_graph(
        nodes_v2,
        "graph_v2",
        lambda edge: (
            edge.part + f": {edge.transport_station.name}"
            if isinstance(edge, process_graphs_tools.EdgeWithTransport)
            else ""
        ),
    )

    # The time of transport between the stations is going to be stimated with the distance between them, the mean speed of the transport stations and the distance between the transport stations and the storage stations

    # Its also particularly important to define the process time of the press activity and the


if __name__ == "__main__":
    get_model_graph()
    get_model_graph_v2()
