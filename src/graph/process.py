import itertools
from typing import Callable, List, get_origin

import prettytable

import model, outputs
from . import PathEdge, StationNode, RoutingGraphEdge


class ManufacturingProcessGraph:

    def __init__(self, system_model: model.ModelSpecification) -> None:
        self.stations_producing_objectives = []
        self.activities_to_be_executed = []
        self.parts_to_be_produced = []

        self.station_nodes: List[StationNode] = []

        self.routing_edges: List[RoutingGraphEdge] = []
        self.pathing_edges: List[PathEdge] = []

        self.system_model = system_model

    def generate_model_graph(self) -> None:
        """
        Generate a graph with all the possible part flows in the plant. For doing that, first we need to know the objective of the process. In this case, the objective is to produce the part 3. We have also available the list of activities that produce each part in the model, we are going to assume that the only part is part3

        """

        parts_to_be_produced = self.system_model.parts
        activities_to_be_executed: List[str] = []

        for part_name in parts_to_be_produced:
            activities_to_be_executed += self.system_model.parts[part_name].activities

        self.parts_to_be_produced = parts_to_be_produced
        self.activities_to_be_executed = activities_to_be_executed

        stations_producing_objectives = []

        for station in self.system_model.stations.models.values():
            if station.activities is None:
                continue

            for activity in station.activities:
                if activity in activities_to_be_executed:
                    stations_producing_objectives.append(station)

        self.stations_producing_objectives = stations_producing_objectives

        # Graph with all the possible part flows. It represents the possible part flows between the stations
        # First we are going to define a node for each station in the plant

        nodes: List[StationNode] = []

        for station in self.system_model.stations.models.values():
            nodes.append(StationNode(station))

        # Then we are going to add edges to the nodes. All edges are going from/to a transport station to/from a storage station. We are going to iterate over the nodes and add the edges to all the other nodes available.

        for transport_node in nodes:

            if transport_node.model.transports is None:
                continue

            for storage_station_node in nodes:
                if storage_station_node.model.storages is None:
                    continue

                for storage_node in storage_station_node.storage_nodes:
                    for storage_type in storage_node.model.type:

                        if storage_type.part in transport_node.model.transports.parts:

                            if storage_type.add == 1:
                                new_edge = RoutingGraphEdge(
                                    storage_type.part,
                                    transport_node,
                                    storage_node,
                                    RoutingGraphEdge.Direction.INPUT,
                                )
                                if new_edge not in transport_node.edges:
                                    storage_node.edges.append(new_edge)
                                    transport_node.edges.append(new_edge)
                                    storage_node.edges.append(new_edge)
                                    self.routing_edges.append(new_edge)

                            if storage_type.remove == 1:
                                new_edge = RoutingGraphEdge(
                                    storage_type.part,
                                    transport_node,
                                    storage_node,
                                    RoutingGraphEdge.Direction.OUTPUT,
                                )
                                if new_edge not in transport_node.edges:
                                    storage_node.edges.append(new_edge)
                                    transport_node.edges.append(new_edge)
                                    storage_node.edges.append(new_edge)
                                    self.routing_edges.append(new_edge)

        self.station_nodes = nodes

        # Now we have to generate the path edges, which represent the routes between storage positions.

        # Loop over the pair of each station storage nodes and all the other storage nodes from the other stations
        for station_node in nodes:
            station_node = station_node
            if station_node.model.storages is None:
                continue
            for storage_node in station_node.storage_nodes:
                for storage_type in storage_node.model.type:
                    # For each storage_type in each storage_node of each station_node

                    # Inner loop over all storage nodes of all the stations except the station_node
                    for other_station_node in nodes:
                        if other_station_node == station_node:
                            continue
                        other_storage_station_node = other_station_node
                        if other_storage_station_node.model.storages is None:
                            continue
                        for other_storage_node in other_station_node.storage_nodes:
                            for other_storage_type in other_storage_node.model.type:

                                # For each other_storage_type in each other_storage_node of each other_station_node
                                if storage_type.part != other_storage_type.part:
                                    continue

                                if storage_type.add and other_storage_type.remove:
                                    new_edge = PathEdge(
                                        storage_type.part,
                                        other_storage_node,
                                        storage_node,
                                    )
                                    if new_edge not in storage_node.pathing_edges:
                                        storage_node.pathing_edges.append(new_edge)
                                        other_storage_node.pathing_edges.append(
                                            new_edge
                                        )
                                        self.pathing_edges.append(new_edge)

                                if storage_type.remove and other_storage_type.add:
                                    new_edge = PathEdge(
                                        storage_type.part,
                                        storage_node,
                                        other_storage_node,
                                    )
                                    if new_edge not in storage_node.pathing_edges:
                                        storage_node.pathing_edges.append(new_edge)
                                        other_storage_node.pathing_edges.append(
                                            new_edge
                                        )
                                        self.pathing_edges.append(new_edge)

    def reset_positions(self) -> None:
        for node in self.station_nodes:
            node.reset_position()

    def print(self) -> None:
        print("Parts to be produced:")
        [print(part) for part in self.parts_to_be_produced]

        print("Activities to be executed:")
        [print(activity) for activity in self.activities_to_be_executed]

        print("Stations producing objectives:")
        [print(station) for station in self.stations_producing_objectives]

        print("Nodes:")
        [print(node) for node in self.station_nodes]

        self.print_directed_graph_table(self.station_nodes)

    def export(self, name) -> None:
        get_origin_id: Callable[[RoutingGraphEdge], str] = lambda edge: (
            edge.transport.id
            if edge.direction == RoutingGraphEdge.Direction.INPUT
            else edge.storage.id
        )
        get_destiny_id: Callable[[RoutingGraphEdge], str] = lambda edge: (
            edge.storage.id
            if edge.direction == RoutingGraphEdge.Direction.INPUT
            else edge.transport.id
        )
        outputs.export_directed_graph(
            self.station_nodes, name, get_origin_id, get_destiny_id
        )

    def print_directed_graph_table(self, nodes: List[StationNode]):
        nodes_table = prettytable.PrettyTable()
        nodes_table._max_width = {
            "Node": 20,
            "Storages": 150,
            "Routing edges": 150,
            "Path edges": 150,
        }

        nodes_table.field_names = ["Node", "Storages", "Routing edges", "Path edges"]

        row = []

        for node in nodes:
            row = [str(node)]
            if len(node.storage_nodes) > 0:
                next_cell = ""
                for storage_node in node.storage_nodes:
                    next_cell += str(storage_node)
                    next_cell += "\n"
                row.append(next_cell)
                next_cell = ""
                for storage_node in node.storage_nodes:
                    for edge in storage_node.edges:
                        next_cell += str(edge)
                        next_cell += "\n"
                row.append(next_cell)
                next_cell = ""
                for storage_node in node.storage_nodes:
                    for edge in storage_node.pathing_edges:
                        next_cell += str(edge)
                        next_cell += "\n"
                row.append(next_cell)

            else:
                edges_cell = ""
                for edge in node.edges:
                    edges_cell += str(edge)
                    edges_cell += "\n"
                row.extend(["", edges_cell, ""])
            nodes_table.add_row(row)

        print(nodes_table)


if __name__ == "__main__":
    import src.model.tools
    from pathlib import Path

    spec = src.model.tools.SystemSpecification()
    spec.read_model_from_source(Path("./model.yaml"))

    flowGraph = ManufacturingProcessGraph(spec.model)

    flowGraph.generate_model_graph()

    flowGraph.print()
    flowGraph.export("manufacturing_graph")
