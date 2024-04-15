from math import pi
import textwrap
import unittest
import pyvisgraph as vg

from __init__ import GridParams, StationModel, StationModelDict
from model.plant import Plant, angle_between_two_points


inout_station_dict: StationModelDict = {
    "Storage": [
        {
            "Type": [{"Part": "Part1", "Add": 0, "Remove": 1}],
            "Place": {"X": 0.0, "Y": 0.0},
        },
        {
            "Type": [{"Part": "Part2", "Add": 0, "Remove": 1}],
            "Place": {"X": 0.0, "Y": 0.0},
        },
        {
            "Type": [{"Part": "Part3", "Add": 1, "Remove": 0}],
            "Place": {"X": 0.0, "Y": 0.0},
        },
    ]
}

storage_station_dict: StationModelDict = StationModelDict(
    Storage=[
        {
            "Type": [{"Part": "Part1", "Add": 1, "Remove": 0}],
            "Place": {"X": 0.0, "Y": 0.0},
        },
        {
            "Type": [{"Part": "Part2", "Add": 1, "Remove": 0}],
            "Place": {"X": 0.2, "Y": 0.2},
        },
        {
            "Type": [{"Part": "Part3", "Add": 0, "Remove": 1}],
            "Place": {"X": 0.4, "Y": 0.4},
        },
    ]
)

press_station_dict: StationModelDict = StationModelDict(
    Storage=[
        {
            "Type": [{"Part": "Part1", "Add": 1, "Remove": 0}],
            "Place": {"X": 0.0, "Y": 0.0},
        },
        {
            "Type": [{"Part": "Part2", "Add": 1, "Remove": 0}],
            "Place": {"X": 0.0, "Y": 0.0},
        },
        {
            "Type": [{"Part": "Part3", "Add": 0, "Remove": 1}],
            "Place": {"X": 0.0, "Y": 0.0},
        },
    ],
    Obstacles=[
        [
            {"X": 0.2, "Y": 0.2},
            {"X": 0.6, "Y": 0.2},
            {"X": 0.6, "Y": 0.2},
            {"X": 0.6, "Y": 0.6},
        ]
    ],
)

robot_station_dict: StationModelDict = StationModelDict(
    Transport={"Range": 2, "Parts": ["Part1", "Part2", "Part3"]},
    Obstacles=[
        [
            {"X": 0.2, "Y": 0.2},
            {"X": 0.6, "Y": 0.2},
            {"X": 0.6, "Y": 0.2},
            {"X": 0.6, "Y": 0.6},
        ]
    ],
)


class TestPointMethods(unittest.TestCase):

    def test_angle_between_two_points(self):
        """Test that the angle between two points is calculated correctly."""
        test_list: list[tuple[vg.Point, vg.Point, float]] = [
            (vg.Point(0, 0), vg.Point(1, 0), 0),
            (vg.Point(0, 0), vg.Point(0, 1), pi / 2),
            (vg.Point(0, 0), vg.Point(1, 1), pi / 4),
            (vg.Point(0, 0), vg.Point(-1, 0), pi),
            (vg.Point(0, 0), vg.Point(0, -1), -pi / 2),
            (vg.Point(0, 0), vg.Point(-1, -1), -3 * pi / 4),
        ]
        for point1, point2, expected in test_list:
            result = angle_between_two_points(point1.x, point1.y, point2)
            self.assertEqual(result, expected)

    def test_plant(self):
        print()
        print(
            textwrap.dedent(
                """
            --------------------
            Test Plant object functions, it's a big test, should be split in smaller tests.
            """
            )
        )
        self.longMessage = True
        plant = Plant(
            GridParams({"Size": {"X": 5, "Y": 5}, "Measures": {"X": 0.8, "Y": 0.8}})
        )

        plant.grid[0][2] = StationModel("InOut", inout_station_dict)
        plant.grid[1][2] = StationModel("Storage", storage_station_dict)
        plant.grid[2][2] = StationModel("Press", press_station_dict)
        plant.grid[1][1] = StationModel("Robot", robot_station_dict)

        plant.build_vis_graphs()

        self.assertIsInstance(plant.vis_graphs["Robot"], vg.Graph, "Graph not built")
        if plant.vis_graphs["Robot"].graph is None:
            return

        self.assertTrue(
            len(plant.vis_graphs["Robot"].graph.edges), "No vertices checked"
        )
        self.assertTrue(
            len(plant.vis_graphs["Robot"].graph.polygons), "No polygons checked"
        )

        visible_points = plant.vis_graphs["Robot"].find_visible(vg.Point(1, 1))

        print("Main graph points: ")
        for point in plant.vis_graphs["Robot"].graph.graph:
            print(point)

        print("Press central point: ")
        print(vg.Point(2, 2))
        print("Robot central point: ")
        print(vg.Point(1, 1))

        print("Visible points: ")
        for point in visible_points:
            print(point)

        self.assertEqual(
            visible_points,
            [vg.Point(2.50, 1.50), vg.Point(1.50, 1.50), vg.Point(1.50, 2.50)],
        )

        print("--------------------")


if __name__ == "__main__":
    unittest.main(verbosity=2)
