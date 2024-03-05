from __future__ import annotations

import datetime
from math import cos, pi, sin
from typing import List, Callable, TYPE_CHECKING
import prettytable

from graph import (
    DirectedGraphEdge,
    DirectedGraphEdgeInterface,
    DirectedGraphNodeInterface,
)
from model import PlantGridType

if TYPE_CHECKING:
    from graph.problem import TreeNode

now = datetime.datetime.now()

# From the date_time variable, you can extract the date in various
# custom formats with .strftime(), for example:
now_string: str = now.strftime("%Y_%m_%d_%H_%M_%S")


import pyvis as vis  # type: ignore
import networkx as nx  # type: ignore


def print_directed_graph_table(nodes: List[DirectedGraphNodeInterface]):
    nodes_table = prettytable.PrettyTable()

    nodes_table.field_names = ["Node", "Outgoing edges"]

    for node in nodes:
        for edge in node.edges:
            nodes_table.add_row([str(node), str(edge)])

    print(nodes_table)


def export_directed_graph(
    nodes: List[DirectedGraphNodeInterface],
    name: str,
    edge_label_generador: Callable[
        [DirectedGraphEdgeInterface], str
    ] = lambda edge: str(edge),
):

    graph_viewer = vis.network.Network(directed=True, height="1000px")
    graph_generator = nx.MultiDiGraph()

    coordinates_generator = circunstripted_penthagon_coordinates_gen(0, 0, 300, 0)

    for node in nodes:
        coordinates = next(coordinates_generator)
        graph_generator.add_node(
            str(node.id),
            label=str(node.id),
            physics=False,
            x=coordinates[0],
            y=coordinates[1],
            size=40,
        )

    for node in nodes:
        for edge in node.edges:
            graph_generator.add_edge(
                str(edge.origin.id),
                str(edge.destiny.id),
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


def export_tree_graph(first_node: TreeNode, name: str):
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
    graph_viewer.save_graph(f"output/history/{now_string}_{name}.html")
    graph_viewer.save_graph(f"output/last_{name}.html")


def add_tree_nodes(
    graph_generator: nx.Graph, previous_node: TreeNode, level: int, initial_x: int
):
    if previous_node.next is None:
        return initial_x

    actual_x = initial_x

    for index, node in enumerate(previous_node.next):
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


def print_plant_grid(plant_grid: PlantGridType, width=15):
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


def circunstripted_penthagon_coordinates_gen(h, k, r, theta):
    i = 0
    while i < 5:
        theta = 2 * pi / 5
        x = h + r * cos(theta + i * (2 * pi / 5))
        y = k + r * sin(theta + i * (2 * pi / 5))
        yield (x, y)
        i += 1
