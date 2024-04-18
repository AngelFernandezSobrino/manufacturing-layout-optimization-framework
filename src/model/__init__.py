from __future__ import annotations

import copy
from dataclasses import dataclass
import itertools
import json
from math import atan2, cos, sin, sqrt
from re import S
from typing import Dict, Generic, List, NotRequired, Optional, TypeVar, TypedDict
import pyvisgraph as vg

IntOrFloat = TypeVar("IntOrFloat", int, float)


class VectorDict(TypedDict, Generic[IntOrFloat]):
    X: IntOrFloat
    Y: IntOrFloat


class Vector(Generic[IntOrFloat]):
    """
    Representation of a position in a 2D plane. It contains the x and y coordinates of the position. It has methods to calculate the distance between two positions and the dot product between two positions.

    Returns:
        _type_: _description_
    """

    def __init__(self, x: IntOrFloat, y: IntOrFloat) -> None:
        self.x: IntOrFloat = x
        self.y: IntOrFloat = y

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    def __add__(self, __value):
        return Vector(self.x + __value.x, self.y + __value.y)

    def __sub__(self, __value):
        return Vector(self.x - __value.x, self.y - __value.y)

    def distance(self) -> float:
        return sqrt(self.x**2 + self.y**2)

    def dot_product(self, __value: Vector) -> float:
        return float(self.x * __value.x + self.y * __value.y)

    def set(self, x: IntOrFloat, y: IntOrFloat) -> None:
        self.x = x
        self.y = y


class ModelSpecification:

    def __init__(
        self,
        model_specification_dict: ModelSpecificationDict,
    ) -> None:
        self.stations: Stations = Stations(model_specification_dict["Stations"])
        self.parts: Dict[str, Part] = {
            part_name: Part(part_name, part_dict)
            for part_name, part_dict in model_specification_dict["Parts"].items()
        }
        self.activities: Dict[str, Activity] = {
            activity_name: Activity(activity_dict)
            for activity_name, activity_dict in model_specification_dict[
                "Activities"
            ].items()
        }


StationNameType = str


class StationModel:

    def __init__(
        self, name: StationNameType, station_model_dict: StationModelDict
    ) -> None:
        self.name = name

        if "Storage" in station_model_dict:
            self.storages = [Storage(s) for s in station_model_dict["Storage"]]
        else:
            self.storages = None

        if "Transport" in station_model_dict:
            self.transports = Transport(station_model_dict["Transport"])
        else:
            self.transports = None

        if "Activities" in station_model_dict:
            self.activities = station_model_dict["Activities"]
        else:
            self.activities = None

        if "Obstacles" in station_model_dict:
            self.obstacles = [
                [vg.Point(v["X"], v["Y"]) for v in o]
                for o in station_model_dict["Obstacles"]
            ]
        else:
            self.obstacles = None

    def __str__(self) -> str:
        return f"{self.name}"

    def render(self):
        return f"{self.name} - {self.storages} - {self.transports} - {self.activities}"

    def toJSON(self):
        return json.dumps(self)

    def get_absolute_obstacles(self, origin: Vector[float]) -> List[List[vg.Point]]:
        return [
            [vg.Point(v.x + origin.x, v.y + origin.y) for v in o]
            for o in self.obstacles  # type: ignore
        ]


class Storage:

    def __init__(
        self,
        storage_dict: StorageDict,
    ) -> None:
        self.type = [
            StorageType(storage_type_dict) for storage_type_dict in storage_dict["Type"]
        ]
        self.position: Vector[float] = Vector(
            storage_dict["Place"]["X"], storage_dict["Place"]["Y"]
        )
        self.id: str = storage_dict["Id"]


class StorageType:

    def __init__(self, storage_type_dict: StorageTypeDict) -> None:
        self.part = storage_type_dict["Part"]
        self.add: int = storage_type_dict["Add"]
        self.remove: int = storage_type_dict["Remove"]
        if "Requires" in storage_type_dict:
            self.requires: List[str] = storage_type_dict["Requires"]
        else:
            self.requires = []

    def __str__(self) -> str:
        return f"{self.part}{'/Add' if self.add == 1 else ''}{'/Remove' if self.remove == 1 else ''}{f'/{self.requires}' if self.requires else ''}"

    def __repr__(self) -> str:
        return self.__str__()


class Transport:

    def __init__(
        self,
        transport_dict: TransportDict,
    ) -> None:
        self.range: float = transport_dict["Range"]
        self.parts: List[str] = transport_dict["Parts"]


class Part:

    def __init__(
        self,
        part_name: str,
        part_dict: PartDict,
    ) -> None:
        self.activities: List[str] = part_dict["Activities"]
        self.name: str = part_name


class Stations:

    def __init__(
        self,
        stations_dict: StationsDict,
    ) -> None:
        self.grid: GridParams = GridParams(stations_dict["Grid"])
        self.models: Dict[StationNameType, StationModel] = {
            k: StationModel(k, v) for k, v in stations_dict["Models"].items()
        }
        self.available_models = set(self.models.keys())


class GridParams:

    def __init__(self, grid_dict: GridParamsDict) -> None:
        self.measures: Vector[float] = Vector(
            grid_dict["Measures"]["X"], grid_dict["Measures"]["Y"]
        )
        self.half_measures = Vector(self.measures.x / 2, self.measures.y / 2)
        self.size: Vector[int] = Vector(grid_dict["Size"]["X"], grid_dict["Size"]["Y"])


class Activity:

    def __init__(
        self,
        activity_dict: ActivityDict,
    ) -> None:
        self.requires = activity_dict["Requires"]
        self.returns = activity_dict["Returns"]
        self.time_spend = activity_dict["TimeSpend"]
        self.requires = None


class StationsDict(TypedDict):
    Grid: GridParamsDict
    Models: Dict[str, StationModelDict]


class GridParamsDict(TypedDict):
    Size: VectorDict[int]
    Measures: VectorDict[float]


class ActivityDict(TypedDict):
    Requires: List[str]
    Returns: List[str]
    TimeSpend: int


class PartDict(TypedDict):
    Activities: List[str]


class TransportDict(TypedDict):
    Range: float
    Parts: List[str]


class ModelSpecificationDict(TypedDict):
    Stations: StationsDict
    Parts: Dict[str, PartDict]
    Activities: Dict[str, ActivityDict]


class StationModelDict(TypedDict):
    Storage: NotRequired[List[StorageDict]]
    Transport: NotRequired[TransportDict]
    Activities: NotRequired[List[str]]
    Obstacles: NotRequired[List[List[VectorDict[float]]]]


class StorageDict(TypedDict):
    Type: List[StorageTypeDict]
    Place: VectorDict[float]
    Id: str


class StorageTypeDict(TypedDict):
    Part: str
    Add: int
    Remove: int
    Requires: NotRequired[List[str]]


ModelsDict = Dict[str, StationModelDict]
