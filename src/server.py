import json
from flask import Flask, request

app = Flask(__name__)

import sys

sys.path.append("./src/")

import outputs
from graph import TreeNode
from graph.process import ManufacturingProcessGraph
from model import StationModel, Vector

from graph import problem as graph_problem
from model import tools as model_tools
from model.tools import get_plant_hash
from support import (
    check_configuration_each_leave,
    check_performance_each_leave,
    populate_next_nodes,
)


@app.route("/")
def redirect_to_editor():
    return app.send_static_file("editor.html")


@app.route("/run", methods=["POST"])
def run():

    spec = model_tools.SystemSpecification()

    data_string = request.get_data().decode()

    spec.read_model_from_string(str(data_string))

    first_node = TreeNode(spec.model.stations.models["InOut"], Vector(2, 0), None)

    populate_next_nodes(first_node, spec.model.stations.models)

    flow_graph = ManufacturingProcessGraph(spec.model)

    flow_graph.generate_model_graph()

    flow_graph.print()
    # flow_graph.export("manufacturing_graph")

    print("Amount of leaves: " + str(first_node.count_leaves()))

    check_configuration_each_leave(first_node, flow_graph)

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

    status = {"best_performance_ratio": 9999999999.0, "best_performance_node": None}

    check_performance_each_leave(first_node, status, flow_graph)

    print("Performance checked")
    print(
        "Count of checked configurations: "
        + str(check_performance_each_leave.count_of_checked_configurations)
    )

    if status["best_performance_node"]:
        plant_grid, _ = graph_problem.create_plant_from_node_with_station_models_used(
            status["best_performance_node"]
        )
        print("Plant hash: " + get_plant_hash(plant_grid))

        # print("Other configurations values: ")
        # print(check_performance_each_leave.other_config_values)

        outputs.print_plant_grid(plant_grid)

        print("Best performance ratio: " + str(status["best_performance_ratio"]))
        print("Best performance node: " + str(status["best_performance_node"]))

    else:
        print("No valid configuration found")

    return json.dumps(plant_grid, default=lambda obj: obj.name)


if __name__ == "__main__":
    app.run()
