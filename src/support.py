from typing import Dict
from graph import TreeNode
from graph.process import ManufacturingProcessGraph
from model import StationModel

import graph.problem as graph_problem
from model.tools import SystemSpecification


def populate_next_nodes(
    node: TreeNode,
    station_models: Dict[str, StationModel],
    spec: SystemSpecification,
    hash_repository: set[set[str]],
):

    plant_grid, station_models_used = (
        graph_problem.create_plant_from_node_with_station_models_used(node, spec)
    )

    available_positions_array = graph_problem.get_available_positions(plant_grid)

    for position in available_positions_array:
        for value in station_models.values():
            if value.name in station_models_used:
                continue

            new_node = TreeNode(value, position, node)

            if node.next is None:
                node.next = []

            new_hash_set = graph_problem.get_hash_for_new_node(new_node, node)

            print(new_hash_set)

            if new_hash_set in hash_repository:
                print("Hash repeated, skipping")
                continue

            node.next.append(new_node)

            populate_next_nodes(new_node, station_models, spec, hash_repository)


def check_configuration_each_leave(
    node: TreeNode, flow_graph: ManufacturingProcessGraph, spec: SystemSpecification
):

    if node.next is None:
        plant_grid, _ = graph_problem.create_plant_from_node_with_station_models_used(
            node, spec
        )

        check_configuration_each_leave.count_of_total_configurations += 1

        if graph_problem.check_configuration_v2(plant_grid, flow_graph):
            # print("Configuration valid")
            check_configuration_each_leave.count_of_valid_configurations += 1
            return True
        else:
            return False

    at_least_one_valid = False

    for index in range(len(node.next) - 1, -1, -1):
        # print(f"Checking {index}")
        if check_configuration_each_leave(node.next[index], flow_graph, spec):
            at_least_one_valid = True
        else:
            del node.next[index]

    return at_least_one_valid


check_configuration_each_leave.count_of_valid_configurations = 0
check_configuration_each_leave.count_of_total_configurations = 0


def check_performance_each_leave(
    node: TreeNode,
    status: dict,
    flow_graph: ManufacturingProcessGraph,
    spec: SystemSpecification,
):
    if node.next is None:
        plant, _ = graph_problem.create_plant_from_node_with_station_models_used(
            node, spec
        )
        check_performance_each_leave.count_of_checked_configurations += 1

        plant_performance = graph_problem.check_performace_v2(plant, flow_graph)

        plant_hash = plant.hash()

        if plant_hash in "InOut(2,0)Robot1(1,1)PartsStorage(2,1)Robot2(3,1)Press(2,2)":
            check_performance_each_leave.other_config_values.append(
                {
                    "plant_performance": plant_performance,
                    "plant_hash": plant_hash,
                }
            )

        if plant_performance < status["best_performance_ratio"]:
            status["best_performance_ratio"] = plant_performance
            status["best_performance_node"] = node

        return

    for next_node in node.next:
        check_performance_each_leave(next_node, status, flow_graph, spec)


check_performance_each_leave.count_of_checked_configurations = 0
check_performance_each_leave.other_config_values = []
