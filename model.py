# import library to read a yaml file
import copy
from dataclasses import dataclass
from typing import Any, Dict, List, TypedDict
import yaml
import prettytable


class TransportType(TypedDict):
    Range: int
    Parts: list[str]


class StorageType(TypedDict):
    Type: list[str]
    Place: Any
    Add: int
    Remove: int


@dataclass
class StationModel:
    name: str
    storage: list[StorageType] | None
    transport: TransportType | None
    activities: list[str] | None

    def __str__(self) -> str:
        return f"{self.name}"


@dataclass
class Position:
    x: int
    y: int

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"


def print_table(plant_grid, width=15):
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


PlantGridType = List[List[StationModel | None]]

station_models: Dict[str, StationModel] = {}

system_model: dict = {}


def get_system_model() -> Dict[str, Any]:
    print("get_system_model")
    if len(system_model) < 1:
        print("read_model_from_source")
        read_model_from_source()

    return copy.deepcopy(system_model)


def get_stations_model() -> Dict[str, StationModel]:
    print("get_stations_model")
    if len(station_models) < 1:
        print("read_model_from_source")
        read_model_from_source()

    return copy.deepcopy(station_models)


def read_model_from_source():
    # Read the model from the yaml file
    model_file = open("model.yaml", "r")
    yaml_parsed = yaml.full_load(model_file)
    for key, value in yaml_parsed["Stations"]["Models"].items():
        station_models[key] = StationModel(
            key,
            value.get("Storage", None),
            value.get("Transport", None),
            value.get("Activities", None),
        )

    global system_model
    system_model = copy.deepcopy(yaml_parsed)


def get_void_plant_grid() -> PlantGridType:
    # 5x5 grid to place the stations

    return [[None for x in range(5)] for y in range(5)]
