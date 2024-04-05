import sys, json

sys.path.append("./src/")


from main import process
from flask import Flask, request

app = Flask(__name__)


@app.route("/")
def redirect_to_editor():
    return app.send_static_file("editor.html")


@app.route("/run", methods=["POST"])
def run():

    data_string = request.get_data().decode()

    plant_grid = process(model_string=data_string)

    return json.dumps(plant_grid, default=lambda obj: obj.name)


if __name__ == "__main__":
    app.run()
