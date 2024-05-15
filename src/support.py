import random
from graph import TreeNode
from graph.process import ManufacturingProcessGraph
from model import StationModel, Vector
from model.plant_graph import GraphPlant
from model.tools import SystemSpecification
import graph.problem as graph_problem


class populate_next_nodes:

    config_repository = [set("")]
    evaluated_nodes = 0
    valid_nodes = 0

    @staticmethod
    def __new__(
        cls,
        node: TreeNode,
        station_models: dict[str, StationModel],
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

        available_positions_array = plant.get_adjacent_positions()

        for position in available_positions_array:
            for value in station_models.values():
                if value.name in station_models_used:
                    continue

                new_node = TreeNode(value, position, node)

                populate_next_nodes(new_node, station_models, spec)


class check_configuration_each_leave:

    count_of_valid_configurations = 0
    count_of_total_configurations = 0
    count_error_configurations = 0
    other_config_values: list = []
    count_of_checked_configurations = 0
    best_performance_ratio = 999999999999999.9
    best_performance_node: TreeNode | None = None

    @staticmethod
    def __new__(
        cls,
        node: TreeNode,
        flow_graph: ManufacturingProcessGraph,
        spec: SystemSpecification,
    ):

        if len(node.next) < 1:
            plant, _ = graph_problem.create_plant_from_node_with_station_models_used(
                node, spec
            )

            check_configuration_each_leave.count_of_total_configurations += 1

            result = graph_problem.check_configuration_v2(plant, flow_graph)

            if result:
                # print("Configuration valid")
                check_configuration_each_leave.count_of_valid_configurations += 1
            else:
                check_configuration_each_leave.count_error_configurations += 1
                return False

            check_configuration_each_leave.count_of_checked_configurations += 1

            if result < check_configuration_each_leave.best_performance_ratio:
                check_configuration_each_leave.best_performance_ratio = result
                check_configuration_each_leave.best_performance_node = node

            return True

        for next_node in node.next:
            check_configuration_each_leave(next_node, flow_graph, spec)

        at_least_one_valid = False

        for index in range(len(node.next) - 1, -1, -1):
            # print(f"Checking {index}")
            if check_configuration_each_leave(node.next[index], flow_graph, spec):
                at_least_one_valid = True
            else:
                del node.next[index]

        return at_least_one_valid


def get_random_plant(system_specification: SystemSpecification):

    plant = GraphPlant(system_specification)
    station_models_used: set[str] = set()

    plant.set_station_location_by_name("InOut", Vector(2, 0))
    station_models_used.add("InOut")

    while True:
        available_positions = plant.get_adjacent_positions()
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

        plant.set_station_location_by_name(station_model.name, position)

        station_models_used.add(station_model.name)

        if station_models_used == system_specification.model.stations.available_models:
            break

    plant.ready()

    return plant


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import pyvisgraph as vg  # pylint disable=import-error

    test_plant = get_random_plant(
        SystemSpecification(model_stream=open("./model.yaml", "r", encoding="utf8"))
    )

    test_plant.render()

    test_plant.build_vis_graphs()

    fig, axes_dict, vis_axes = test_plant.plot_plant_graph()

    for station_name, axes in axes_dict.items():
        path_x = []
        path_y = []

        for point in test_plant.shortest_path(
            station_name, vg.Point(0, 0), vg.Point(2, 2)
        ):
            path_x.append(point.x)
            path_y.append(point.y)

        axes.plot(path_x, path_y, color="red")

    mngr = plt.get_current_fig_manager()
    if mngr is not None:
        mngr.window.attributes("-zoomed", True)
    plt.show()
