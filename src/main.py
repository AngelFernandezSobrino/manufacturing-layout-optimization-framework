from io import TextIOWrapper
from pathlib import Path
import sys
from typing import Dict, List

sys.path.append("./src/")
sys.path.append("./")

import model
import outputs
from graph import TreeNode
from graph.process import ManufacturingProcessGraph
from model import StationModel, Vector

from graph import problem as graph_problem
from model import tools as model_tools
from support import (
    check_configuration_each_leave,
    check_performance_each_leave,
    populate_next_nodes,
)


"""The position 0, 3 is the center of the first row, and has to contain the InOut station

The next step is to place one of the remaining stations in the grid, in a position that has to be nearby some of the previous stations. First of all, we need to know the possible positions for the station. For we iterate over the grid and check if the position is empty and if the some position nearby is not empty. To create all the different configurations we are going to build a tree of configurations. Starting from the initial conditions, with the InOut station on the top-middle position.

Now we have the tree of configurations, we need to check if the configuration is valid or not. To do that, we need to check if part1 and part2 can reach Press station from InOut station and that part3 can reach InOut station from Press station. As the robot can move the three parts, we onli need to check if part1 can reach Press station from InOut station
To do that we need to check if the robot can reach the desired stations.

In that case, it is check by the distance between the stations and the range of the robot, in that case, the robot has to be next to the station to be able to reach it. To check that, we are going to search for the robot in a given configuration and the check is the Press station and the InOut station are in the neighborhood of the robot. To do that, we are going to create a function that returns the position of the robot in a given configuration. Now we have the position of the robot, we can check if the Press station and the InOut station are in the neighborhood of the robot

Now we need to check each configuration to evaluate the cost of the configuration. This function will be able to get a performance ratio for a given configuration. That's the biggest problem, actually. We will start with a simpler, easier to calculate, performance ratio. That would be improved in the future.

graphs.nodes_v2 is a graph that contains all the storage nodes and the parts that can be transferred between them. Now we have to evaluate each part transfer, looking for the length of the path and how much far away is the robot from the nodes. With that information we can do an estimation of the time required for the path to be completed
With al the paths evaluated, we can calculate the performance ratio. The performance ratio would be directly proportional to the system productivity, although it is not the same,
but it is a good ratio that we can use for the comparison of the different configurations

The real part path time and the real performance ratio could be later calculated, but it is not the objective as this result is good enough for the comparison. A pathfinding algorithm could be used to calculate the real path time, and then having the shorter paths available would contribute to a better performance ratio. The only problem is the ponderation of the different paths. It is more important to have a shorter path for a transfer that is done more frequently than for a transfer that is done less frequently. Some of the paths require to be done at least once. Other paths are no required, but they could be used for the system to be more flexible.

For example, intermediate storage places can be used as a buffer for the system, considering that the parts input ratio is not constant. In systems with important variations in the parts input ratio can be specially problematic. Considering each edge in graph.nodes_v2, we are going to iterate through all the configurations and calculate the performance ratio for each configuration

"""


def process(model_string: str = "", model_stream: TextIOWrapper | None = None):

    spec = model_tools.SystemSpecification(
        model_string=model_string, model_stream=model_stream
    )
    flow_graph = ManufacturingProcessGraph(spec.model)

    flow_graph.generate_model_graph()

    flow_graph.print()

    first_node = TreeNode(spec.model.stations.models["InOut"], Vector(2, 0), None)

    hash_repository: set[set[str]] = set()

    populate_next_nodes(first_node, spec.model.stations.models, spec, hash_repository)

    check_configuration_each_leave(first_node, flow_graph, spec)

    print("Configurations checked")

    print(
        "Count of valid configurations: "
        + str(check_configuration_each_leave.count_of_valid_configurations)
    )
    print(
        "Count of total configurations: "
        + str(check_configuration_each_leave.count_of_total_configurations)
    )
    print(
        "Rate of valid configurations: "
        + str(
            check_configuration_each_leave.count_of_valid_configurations
            / check_configuration_each_leave.count_of_total_configurations
        )
    )

    # Print graph again

    status = {"best_performance_ratio": 9999999999.0, "best_performance_node": None}

    check_performance_each_leave(first_node, status, flow_graph, spec)

    print("Performance checked")
    print(
        "Count of checked configurations: "
        + str(check_performance_each_leave.count_of_checked_configurations)
    )

    if status["best_performance_node"]:
        plant_grid, _ = graph_problem.create_plant_from_node_with_station_models_used(
            status["best_performance_node"], spec
        )

        outputs.print_plant_grid(plant_grid)

        print("Best performance ratio: " + str(status["best_performance_ratio"]))
        print("Best performance node: " + str(status["best_performance_node"]))

    else:
        print("No valid configuration found")

    return plant_grid


def export(first_node, flow_graph: ManufacturingProcessGraph):
    outputs.export_tree_graph(first_node, "tree")
    flow_graph.export("manufacturing_graph")


if __name__ == "__main__":

    model_file = open("./model.yaml", "r")

    process(model_stream=model_file)
