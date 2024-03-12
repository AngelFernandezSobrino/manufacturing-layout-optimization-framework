import itertools
from typing import List

import model, outputs
from . import PathEdge, StationNode, RoutingGraphEdge


class ManufacturingProcessGraph:

    def __init__(self, system_model: model.ModelSpecification) -> None:
        self.stations_producing_objectives = None
        self.activities_to_be_executed = None
        self.parts_to_be_produced = None
        self.station_nodes: List[StationNode] = []
        self.routing_edges: List[RoutingGraphEdge] = []
        self.path_edges: List[PathEdge] = []

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

        for node in nodes:
            node.edges = []
            if node.model.transports is None:
                continue
            transport_node = node

            for other_node in nodes:
                if other_node.model.storages is None:
                    continue

                for storage_index, storage_node in enumerate(other_node.storage_nodes):
                    for storage_type in storage_node.storage.type:

                        if storage_type in transport_node.model.transports.parts:
                            if storage_node.storage.remove == 1:
                                new_edge = RoutingGraphEdge(
                                    storage_type, storage_node, transport_node
                                )
                                if new_edge not in transport_node.edges:
                                    other_node.edges.append(new_edge)
                                    transport_node.edges.append(new_edge)
                                    storage_node.routing_edges.append(new_edge)
                                    self.routing_edges.append(new_edge)

                            if storage_node.storage.add == 1:
                                new_edge = RoutingGraphEdge(
                                    storage_type, transport_node, other_node
                                )
                                if new_edge not in transport_node.edges:
                                    other_node.edges.append(new_edge)
                                    transport_node.edges.append(new_edge)
                                    storage_node.routing_edges.append(new_edge)
                                    self.routing_edges.append(new_edge)

        self.station_nodes = nodes

        # Now we have to generate the path edges, which represent the routes between storage positions.

        for node in nodes:
            if node.model.storages is None:
                continue

            for storage_node in node.storage_nodes:
                for other_node in nodes:
                    if other_node.model.storages is None:
                        continue

                    for other_storage_node in other_node.storage_nodes:
                        if storage_node.storage is other_storage_node.storage:
                            continue
                        if storage_node.storage.type != other_storage_node.storage.type:
                            continue
                        if (
                            storage_node.storage.add == 1
                            and other_storage_node.storage.remove == 1
                        ):
                            new_edge = PathEdge(
                                storage_node.storage.type,
                                other_storage_node,
                                storage_node,
                            )
                            if new_edge not in storage_node.pathing_edges:
                                storage_node.pathing_edges.append(new_edge)
                                other_storage_node.pathing_edges.append(new_edge)
                                self.path_edges.append(new_edge)

                        if (
                            storage_node.storage.remove == 1
                            and other_storage_node.storage.add == 1
                        ):
                            new_edge = PathEdge(
                                storage_node.storage.type,
                                storage_node,
                                other_storage_node,
                            )
                            if new_edge not in storage_node.pathing_edges:
                                storage_node.pathing_edges.append(new_edge)
                                other_storage_node.pathing_edges.append(new_edge)
                                self.path_edges.append(new_edge)

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

        outputs.print_directed_graph_table(self.station_nodes)

    def export(self, name) -> None:
        outputs.export_directed_graph(self.station_nodes, name)


if __name__ == "__main__":
    import src.model.tools
    from pathlib import Path

    spec = src.model.tools.SystemSpecification(Path("./model.yaml"))

    flowGraph = ManufacturingProcessGraph(spec.model)

    flowGraph.generate_model_graph()

    flowGraph.print()
    flowGraph.export("manufacturing_graph")
