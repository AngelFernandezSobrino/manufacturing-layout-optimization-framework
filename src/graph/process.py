from typing import List

from src import model, outputs
from . import ProcessGraphNode, ProcessGraphEdge


class ManufacturingProcessGraph:

    def __init__(self, system_model: model.ModelSpecification) -> None:
        self.stations_producing_objectives = None
        self.activities_to_be_executed = None
        self.parts_to_be_produced = None
        self.nodes: List[ProcessGraphNode] = []

        self.edges: List[ProcessGraphEdge] = []

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

        nodes: List[ProcessGraphNode] = []

        for station in self.system_model.stations.models.values():
            nodes.append(ProcessGraphNode(station))

        # Then we are going to add edges to the nodes. All edges are going from/to a transport station to/from a storage station. We are going to iterate over the nodes and add the edges to all the other nodes available.

        for transport_node in nodes:
            transport_node.edges = []
            if transport_node.station.transport is None:
                continue

            for other_node in nodes:
                if other_node.station.storage is None:
                    continue
                for storage in other_node.station.storage:
                    for storage_type in storage.type:
                        if storage_type in transport_node.station.transport.parts:
                            if storage.remove == 1:
                                new_edge = ProcessGraphEdge(
                                    storage_type, transport_node, other_node
                                )
                                if new_edge not in other_node.edges:
                                    other_node.edges.append(new_edge)
                                    self.edges.append(new_edge)

                            if storage.add == 1:
                                new_edge = ProcessGraphEdge(
                                    storage_type, transport_node, transport_node
                                )
                                if new_edge not in transport_node.edges:
                                    transport_node.edges.append(new_edge)
                                    self.edges.append(new_edge)
        self.nodes = nodes



    def reset_positions(self) -> None:
        for node in self.nodes:
            node.reset_position()

    def print(self) -> None:
        print("Parts to be produced:")
        [print(part) for part in self.parts_to_be_produced]

        print("Activities to be executed:")
        [print(activity) for activity in self.activities_to_be_executed]

        print("Stations producing objectives:")
        [print(station) for station in self.stations_producing_objectives]

        print("Nodes:")
        [print(node) for node in self.nodes]

        outputs.print_directed_graph_table(self.nodes)

    def export(self, name) -> None:
        outputs.export_directed_graph(self.nodes, name)


# def get_model_graph(system_model: src.model.ModelSpec):

#     parts_to_be_produced = system_model.Parts
#     activities_to_be_executed: List[str]

#     for part_name in parts_to_be_produced:
#         activities_to_be_executed += system_model.Parts[part_name].Activities

#     print("Parts to be produced:")
#     [print(part) for part in parts_to_be_produced]

#     print("Activities to be executed:")
#     [print(activity) for activity in activities_to_be_executed]

#     stations_producing_objectives = []

#     for station in system_model.Stations.models.values():
#         if station.Activities is None:
#             continue

#         for activity in station.Activities:
#             if activity in activities_to_be_executed:
#                 stations_producing_objectives.append(station)

#     print("Stations producing objectives:")
#     [print(station) for station in stations_producing_objectives]

#     # Graph with all the possible part flows. It represents the possible part flows between the stations

#     # First we are going to define a node for each station in the plant

#     nodes: List[ProcessGraphNode] = []

#     for station in system_model.Stations.models.values():
#         nodes.append(ProcessGraphNode(station))

#     print("Nodes:")
#     [print(node) for node in nodes]

#     # Then we are going to add edges to the nodes. All edges are going from/to a transport station to/from a storage station. We are going to iterate over the nodes and add the edges to all the other nodes available.

#     for transport_node in nodes:
#         transport_node.edges = []
#         if transport_node.station.Transport is None:
#             continue

#         for other_node in nodes:
#             if other_node.station.Storage is None:
#                 continue
#             for storage in other_node.station.Storage:
#                 for type in storage.Type:
#                     if type in transport_node.station.Transport.Parts:
#                         if storage.Remove == 1:
#                             new_edge = ProcessGraphEdge(type, other_node)
#                             if new_edge not in other_node.edges:
#                                 other_node.edges.append(new_edge)

#                         if storage.Add == 1:
#                             new_edge = ProcessGraphEdge(type, transport_node)
#                             if new_edge not in transport_node.edges:
#                                 transport_node.edges.append(new_edge)

#     print_directed_graph_table(nodes)

#     export_directed_graph(nodes, "graph")

#     return nodes


# def get_model_graph_v2():

#     # Vamos a probar con otra version, en este caso en el grafo solo hay nodos de almacenamiento, y las aristas son el transporte(TODO: Translate to english, sorry xd, I mixed the languages)

#     # We need a class to represent the edges of the graph, it would contain the part, the destination node and the transport station used

#     # First we should generate a dict with all the parts in the model and the transport stations that<z can transport them

#     station_models = model.get_stations_model()
#     system_model = model.get_system_model()

#     parts_transport_stations: Dict[str, List[model.StationModel]] = {}

#     for station in station_models.values():
#         if station.transport is not None:
#             for part in station.transport["Parts"]:
#                 if part not in parts_transport_stations:
#                     parts_transport_stations[part] = []
#                 parts_transport_stations[part].append(station)

#     # We are going to define a node for each station in the plant

#     nodes_v2: List[process_graphs_tools.StationNode] = []

#     for station in station_models.values():
#         if station.storage is not None:
#             nodes_v2.append(process_graphs_tools.StationNode(station, []))

#     # Now we are going to add edges to the nodes_v2
#     # All edges are going from/to a transport station to/from a storage station
#     # We are going to iterate over the nodes_v2 and add the edges to all the other nodes_v2 available

#     for node in nodes_v2:
#         node.outgoing_edges = []

#         for other_node in nodes_v2:
#             if (
#                 node.station.name == other_node.station.name
#                 or node.station.storage is None
#             ):
#                 continue
#             for storage_slot in node.station.storage:
#                 if storage_slot["Remove"] != 1:
#                     continue
#                 for part in storage_slot["Type"]:
#                     if other_node.station.storage is None:
#                         continue
#                     for other_storage_slot in other_node.station.storage:
#                         if other_storage_slot["Add"] != 1:
#                             continue
#                         for other_part in other_storage_slot["Type"]:
#                             if part != other_part:
#                                 continue
#                             for transport_station in parts_transport_stations[part]:
#                                 new_edge_with_transport = (
#                                     process_graphs_tools.EdgeWithTransport(
#                                         part, other_node, transport_station
#                                     )
#                                 )
#                                 if new_edge_with_transport in node.outgoing_edges:
#                                     continue
#                                 node.outgoing_edges.append(new_edge_with_transport)

#     print_nodes_table(nodes_v2)

#     export_process_graph(
#         nodes_v2,
#         "graph_v2",
#         lambda edge: (
#             edge.part + f": {edge.transport_station.name}"
#             if isinstance(edge, process_graphs_tools.EdgeWithTransport)
#             else ""
#         ),
#     )

# The time of transport between the stations is going to be estimated with the distance between them, the mean speed of the transport stations and the distance between the transport stations and the storage stations

# Its also particularly important to define the process time of the press activity and the


if __name__ == "__main__":
    import src.model.tools
    from pathlib import Path

    spec = src.model.tools.SystemSpecification(Path("./model.yaml"))

    flowGraph = ManufacturingProcessGraph(spec.model)

    flowGraph.generate_model_graph()

    flowGraph.print()
    flowGraph.export("manufacturing_graph")

    # get_model_graph_v2()
