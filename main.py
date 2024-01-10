# import library to read a yaml file
from asyncio import Transport
from ctypes import Array
from dataclasses import dataclass
from os import name
import random
import stat
from typing import List
import yaml
import prettytable

model_file = open("model.yaml", "r")

model = yaml.full_load(model_file)

stationModels = {}


@dataclass
class StationModel:
    name: str
    storage: dict
    transport: dict
    activities: dict

    def __str__(self) -> str:
        return f"{self.name} {hex(id(self))}"


for key, value in model["Stations"]["Models"].items():
    stationModels[key] = StationModel(
        key,
        value.get("Storage", None),
        value.get("Transport", None),
        value.get("Activities"),
    )

[print(model) for model in stationModels.values()]

# Model consist on stations and properties
# The first step would be to generate a 5x5 grid to place the stations


plant_grid_type = List[List[StationModel | None]]

plant_grid: plant_grid_type = [[None for x in range(5)] for y in range(5)]

# The position 0, 3 is the center of the first row, and has to contain the InOut station

plant_grid[0][2] = stationModels.pop("InOut")

# Print plant grid

table = prettytable.PrettyTable()

column_names = ["", "0", "1", "2", "3", "4"]
table_width: dict[str, int] = {}

for name in column_names:
    table_width[name] = 15

table.field_names = column_names
table._max_width = table_width
table._min_width = table_width

for row_index, row in enumerate(plant_grid):
    table.add_row([row_index, *row])

print(table)


[print(model) for model in stationModels.values()]

# The next step is to place one of the remaining stations in the grid, in a position that has to be nearby some of the previous stations<F

# First of all, we need to know the possible positions for the station. For we iterate over the grid and check if the position is empty and if the some position nearby is not empty


@dataclass
class Position:
    x: int
    y: int

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"


available_positions_array: List[Position] = []
available_positions_grid: List[List[int]] = [[0 for x in range(5)] for y in range(5)]

for position in available_positions_array:
    available_positions_grid[position.y][position.x] = 1

for y in range(1, 5):
    for x in range(5):
        if plant_grid[y][x] is None:
            if (
                (plant_grid[y - 1][x] is not None)
                or (x > 0 and plant_grid[y][x - 1] is not None)
                or (x < 4 and plant_grid[y][x + 1] is not None)
                or (y < 4 and plant_grid[y + 1][x] is not None)
                or (x > 0 and plant_grid[y - 1][x - 1] is not None)
                or (x < 4 and plant_grid[y - 1][x + 1] is not None)
                or (y < 4 and x > 0 and plant_grid[y + 1][x - 1] is not None)
                or (y < 4 and x < 4 and plant_grid[y + 1][x + 1] is not None)
            ):
                available_positions_grid[y][x] = 1
                available_positions_array.append(Position(x, y))


available_positions_table = prettytable.PrettyTable()

for name in column_names:
    table_width[name] = 5

available_positions_table.field_names = column_names
available_positions_table._max_width = table_width
available_positions_table._min_width = table_width

for row_index, row in enumerate(available_positions_grid):
    available_positions_table.add_row([row_index, *row])

print(available_positions_table)

print("[", end="")
for position in available_positions_array:
    print(position, end="")
    print(", ", end="")

print("]")

# Now we have the available positions, we can choose one of them randomly

# The number of available position is the length of the array available_positions_array
# We need a random number between 0 and the length of the array - 1

random_position_index = random.randint(0, len(available_positions_array) - 1)

print(f"Random position index: {random_position_index}")

# Now we have the index, we can get the position

random_position = available_positions_array[random_position_index]

print(f"Random position: {random_position}")

# Now we have the position, we can choose one of the remaining stations randomly

# The number of remaining stations is the length of the array stationModels

random_station_index = random.randint(0, len(stationModels) - 1)

print(f"Random station index: {random_station_index}")

# Now we have the index, we can get the station

random_station = list(stationModels.values())[random_station_index]

print(f"Random station: {random_station}")

# Now we have the position and the station, we can place the station in the grid

plant_grid[random_position.y][random_position.x] = random_station

