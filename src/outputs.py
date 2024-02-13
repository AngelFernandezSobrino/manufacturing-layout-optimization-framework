import datetime
from math import cos, pi, sin
from typing import Callable, List

import prettytable

from src import process_graphs_tools
import src

now = datetime.datetime.now()

# From the date_time variable, you can extract the date in various
# custom formats with .strftime(), for example:
now_string: str = now.strftime("%Y_%m_%d_%H_%M_%S")


import pyvis as vis  # type: ignore
import networkx as nx  # type: ignore


def print_nodes_table(nodes: List[process_graphs_tools.StationNode]):
    nodes_table = prettytable.PrettyTable()

    nodes_table.field_names = ["Node", "Outgoing edges"]

    for node in nodes:
        for edge in node.outgoing_edges:
            nodes_table.add_row([str(node), str(edge)])

    print(nodes_table)


def export_process_graph(
    nodes: List[process_graphs_tools.StationNode],
    name: str,
    edge_label_generador: Callable[
        [process_graphs_tools.Edge | process_graphs_tools.EdgeWithTransport], str
    ] = lambda edge: edge.part,
):

    graph_viewer = vis.network.Network(directed=True, height="1000px")
    graph_generator = nx.MultiDiGraph()

    coordinates_generator = circunstripted_penthagon_coordinates_gen(0, 0, 300, 0)

    for node in nodes:
        coordinates = next(coordinates_generator)
        graph_generator.add_node(
            str(node.station.name),
            label=str(node.station.name),
            physics=False,
            x=coordinates[0],
            y=coordinates[1],
            size=40,
        )

    for node in nodes:
        for edge in node.outgoing_edges:
            graph_generator.add_edge(
                str(node.station.name),
                str(edge.destination.station.name),
                label=edge_label_generador(edge),
            )

    # graph_viewer.toggle_physics(False)
    graph_viewer.from_nx(graph_generator)
    graph_viewer.barnes_hut(
        gravity=-2000,
        central_gravity=0.3,
        spring_length=100,
        damping=0.09,
        overlap=0.1,
    )
    # graph_viewer.set_edge_smooth('dynamic')
    graph_viewer.save_graph(f"output/last_{name}.html")
    graph_viewer.save_graph(f"output/history/{now_string}_{name}.html")


def circunstripted_penthagon_coordinates_gen(h, k, r, theta):
    i = 0
    while i < 5:
        theta = 2 * pi / 5
        x = h + r * cos(theta + i * (2 * pi / 5))
        y = k + r * sin(theta + i * (2 * pi / 5))
        yield (x, y)
        i += 1


def export_tree_graph(first_node: src.solver_graph.Node):
    graph_viewer = vis.network.Network(height="1000px")
    graph_generator = nx.Graph()

    graph_generator.add_node(
        id(first_node),
        label=(first_node.station.name + str(first_node.position)),
        physics=False,
        x=0,
        y=0,
    )

    add_tree_nodes(
        graph_generator=graph_generator, previous_node=first_node, level=1, initial_x=0
    )

    # graph_viewer.toggle_physics(False)
    graph_viewer.from_nx(graph_generator)
    graph_viewer.barnes_hut(
        gravity=0, central_gravity=0.3, spring_length=100, damping=0.09, overlap=0.1
    )
    # graph_viewer.set_edge_smooth('dynamic')
    graph_viewer.save_graph(f"output/history/{now_string}_tree.html")
    graph_viewer.save_graph(f"output/last_tree.html")


def add_tree_nodes(
    graph_generator: nx.Graph,
    previous_node: src.solver_graph.Node,
    level: int,
    initial_x: int,
):
    if previous_node.next_nodes is None:
        return initial_x

    actual_x = initial_x

    for index, node in enumerate(previous_node.next_nodes):
        graph_generator.add_node(
            id(node),
            label=f"{node.station.name}:{node.position}",
            physics=False,
            x=actual_x * 60,
            y=level * 200 - index % 4 * 20,
        )
        graph_generator.add_edge(
            id(previous_node),
            id(node),
        )
        actual_x = add_tree_nodes(graph_generator, node, level + 1, actual_x)
        actual_x += 1

    return actual_x
