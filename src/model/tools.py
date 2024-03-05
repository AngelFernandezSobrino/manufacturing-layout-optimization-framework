from __future__ import annotations

# import library to read a yaml file
import copy
from pathlib import Path
from types import MappingProxyType
from typing import Dict
import yaml


from . import (
    ModelSpecification,
    StationModel,
    Stations,
    Vector,
    PlantGridType,
    ModelSpecificationDict,
)


class SystemSpecification:

    def __init__(self, model_path: Path) -> None:

        self.path = model_path

        self.model: ModelSpecification = read_model_from_source(self.path)


def read_model_from_source(model_path: Path) -> ModelSpecification:
    # Read the model from the yaml file
    model_file = open(model_path, "r")
    yaml_parsed: ModelSpecificationDict = yaml.full_load(model_file)

    return ModelSpecification(yaml_parsed)


def get_void_plant_grid() -> PlantGridType:
    # 5x5 grid to place the stations

    return [[None for x in range(5)] for y in range(5)]


def get_plant_hash(plant_grid: PlantGridType) -> str:
    plant_hash = ""
    for y in range(5):
        for x in range(5):
            if plant_grid[y][x] is not None:
                plant_hash += f"{plant_grid[y][x].name}({x},{y})"

    return plant_hash