import random
from typing import Dict
from graph import TreeNode
from graph.process import ManufacturingProcessGraph
from model import StationModel

import graph.problem as graph_problem
from model.plant import Plant
from model.tools import SystemSpecification


def populate_next_nodes(
    node: TreeNode,
    station_models: Dict[str, StationModel],
    spec: SystemSpecification,
    # config_repository: set[set[str]],
):
    """Generate search tree of possible configurations

    It generates the tree recursively. It creates a new node for each station model that could be placed in the plant, and then calls itself with the new node.
    To avoid infinite loops, it keeps track of the station models that have already been used in the current branch of the tree.
    It also keeps track of the configurations that have already been generated, to avoid duplicates.
    To do so, it uses a set of strings, where each string represents a configuration of the plant. Once the new node is created, it is set as a child of the current node, but the current node is not set as a parent of the new node. Then the function calls itself with the new node as an argument.
    At the beginning of the function, it creates a new plant from the new node previously created (it only requires child nodes to have their parent defined). Then this plant is compared to the repo and if it is a new configuration that didn't exist the new_node is set as a child of its parent node.
    Otherwise, the function terminates, and the new node is then distroyed because its reference is lost and its, theoretically, parent didn't have a reference to it.
    """
    populate_next_nodes.evaluated_nodes += 1

    plant, station_models_used = (
        graph_problem.create_plant_from_node_with_station_models_used(node, spec)
    )

    new_config_set = plant.get_config_set()

    for config_set in populate_next_nodes.config_repository:
        if new_config_set == config_set:
            return

    populate_next_nodes.config_repository.append(new_config_set)
    populate_next_nodes.valid_nodes += 1

    if node.previous is not None:
        node.previous.next.append(node)

    available_positions_array = graph_problem.get_available_positions(plant)

    for position in available_positions_array:
        for value in station_models.values():
            if value.name in station_models_used:
                continue

            new_node = TreeNode(value, position, node)

            populate_next_nodes(new_node, station_models, spec)


populate_next_nodes.config_repository = [set("")]
populate_next_nodes.evaluated_nodes = 0
populate_next_nodes.valid_nodes = 0


def check_configuration_each_leave(
    node: TreeNode, flow_graph: ManufacturingProcessGraph, spec: SystemSpecification
):

    if not len(node.next):
        plant_grid, _ = graph_problem.create_plant_from_node_with_station_models_used(
            node, spec
        )

        check_configuration_each_leave.count_of_total_configurations += 1
        try:
            if graph_problem.check_configuration_v2(plant_grid, flow_graph):
                # print("Configuration valid")
                check_configuration_each_leave.count_of_valid_configurations += 1
                return True
            else:
                return False
        except Exception as e:
            check_configuration_each_leave.count_error_configurations += 1

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
check_configuration_each_leave.count_error_configurations = 0


def check_performance_each_leave(
    node: TreeNode,
    status: dict,
    flow_graph: ManufacturingProcessGraph,
    spec: SystemSpecification,
):
    if not len(node.next):
        plant, _ = graph_problem.create_plant_from_node_with_station_models_used(
            node, spec
        )
        check_performance_each_leave.count_of_checked_configurations += 1

        plant_performance = graph_problem.check_performace_v2(plant, flow_graph)

        if plant_performance < status["best_performance_ratio"]:
            status["best_performance_ratio"] = plant_performance
            status["best_performance_node"] = node

        return

    for next_node in node.next:
        check_performance_each_leave(next_node, status, flow_graph, spec)


check_performance_each_leave.count_of_checked_configurations = 0
check_performance_each_leave.other_config_values = []


def get_random_plant(system_specification: SystemSpecification):

    plant = Plant(system_specification.model.stations.grid)
    station_models_used: set[str] = set()

    plant.grid[0][2] = system_specification.model.stations.models["InOut"]
    station_models_used.add("InOut")

    while True:
        available_positions = graph_problem.get_available_positions(plant)
        # Get randome value from available_positions list
        position = available_positions[random.choice(range(len(available_positions)))]
        station_model = system_specification.model.stations.models[
            random.choice(
                tuple(
                    system_specification.model.stations.available_models
                    - station_models_used
                )
            )
        ]

        plant.grid[position.y][position.x] = station_model

        station_models_used.add(station_model.name)

        if station_models_used == system_specification.model.stations.available_models:
            break

    plant.ready()

    return plant


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import matplotlib.axes
    import matplotlib
    import pyvisgraph as vg

    plant = get_random_plant(
        SystemSpecification(model_stream=open("./model.yaml", "r"))
    )

    plant.print()

    plant.build_vis_graphs()

    fig, axes_dict, vis_axes = plant.plot_plant_graph()

    for station_name, axes in axes_dict.items():
        path_x = []
        path_y = []

        for point in plant.vis_graphs[station_name].shortest_path(
            vg.Point(0, 0), destination=vg.Point(2, 2)
        ):
            path_x.append(point.x)
            path_y.append(point.y)

        axes.plot(path_x, path_y, color="red")

    mngr = plt.get_current_fig_manager()
    mngr.window.attributes("-zoomed", True)
    plt.show()
