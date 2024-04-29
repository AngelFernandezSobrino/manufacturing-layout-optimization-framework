"""Models
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
import json
from math import sqrt
from typing import Generic, NotRequired, Optional, TypeVar, TypedDict, overload

import pyvisgraph as vg  # type: ignore

IntOrFloat = TypeVar("IntOrFloat", int, float)


class VectorDict(
    TypedDict, Generic[IntOrFloat]
):  # pylint: disable=missing-class-docstring
    X: IntOrFloat
    Y: IntOrFloat


class Vector(Generic[IntOrFloat]):
    """
    Representation of a position in a 2D plane. It contains the x and y coordinates of the position. It has methods to calculate the distance between two positions and the dot product between two positions.

    Returns:
        _type_: _description_
    """

    # pylint: disable=missing-function-docstring

    def __init__(self, x: IntOrFloat, y: IntOrFloat) -> None:
        self.x: IntOrFloat = x
        self.y: IntOrFloat = y

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    def __repr__(self) -> str:
        return self.__str__()

    def equal(self, __value: Vector[IntOrFloat]) -> bool:
        return self.x == __value.x and self.y == __value.y

    def __add__(self, __value: Vector[float]) -> Vector[float]:
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
    """Contains all models in a specification"""

    def __init__(
        self,
        model_specification_dict: ModelSpecificationDict,
    ) -> None:
        self.stations: Stations = Stations(model_specification_dict["Stations"])
        self.parts: dict[str, Part] = {
            part_name: Part(part_name, part_dict)
            for part_name, part_dict in model_specification_dict["Parts"].items()
        }
        self.activities: dict[str, Activity] = {
            activity_name: Activity(activity_dict)
            for activity_name, activity_dict in model_specification_dict[
                "Activities"
            ].items()
        }


StationNameType = str


class StationModel:
    """Contains a model of a station"""

    def __init__(
        self, name: StationNameType, station_model_dict: StationModelDict
    ) -> None:
        self.name = name

        self.storages: Optional[list[Storage]]
        self.transports: Optional[Transport]
        self.activities: Optional[list[str]]
        self.obstacles: Optional[list[list[vg.Point]]]

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

    def render(self):  # pylance: disable=missing_function_docstring
        return f"{self.name} - {self.storages} - {self.transports} - {self.activities}"

    def toJSON(self):  # pylance: disable=missing_function_docstring
        return json.dumps(self)

    def get_absolute_obstacles(self, origin: Vector[float]) -> list[list[vg.Point]]:
        """Gets all obstacles of a station model with absolute positions

        Args:
            origin (Vector[float]): _description_

        Returns:
            list[list[vg.Point]]: _description_
        """
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
            self.requires: list[str] = storage_type_dict["Requires"]
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
        self.parts: list[str] = transport_dict["Parts"]


class Part:

    def __init__(
        self,
        part_name: str,
        part_dict: PartDict,
    ) -> None:
        self.activities: list[str] = part_dict["Activities"]
        self.name: str = part_name


class Stations:

    def __init__(
        self,
        stations_dict: StationsDict,
    ) -> None:
        self.grid: GridParams = GridParams(stations_dict["Grid"])
        self.models: dict[StationNameType, StationModel] = {
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
        self.requires = activity_dict["Requires"]


# pylint: disable=missing-class-docstring


class StationsDict(TypedDict):
    Grid: GridParamsDict
    Models: dict[str, StationModelDict]


class GridParamsDict(TypedDict):
    Size: VectorDict[int]
    Measures: VectorDict[float]


class ActivityDict(TypedDict):
    Requires: list[str]
    Returns: list[str]
    TimeSpend: int


class PartDict(TypedDict):
    Activities: list[str]


class TransportDict(TypedDict):
    Range: float
    Parts: list[str]


class ModelSpecificationDict(TypedDict):
    Stations: StationsDict
    Parts: dict[str, PartDict]
    Activities: dict[str, ActivityDict]


class StationModelDict(TypedDict):
    Storage: NotRequired[list[StorageDict]]
    Transport: NotRequired[TransportDict]
    Activities: NotRequired[list[str]]
    Obstacles: NotRequired[list[list[VectorDict[float]]]]


class StorageDict(TypedDict):
    Type: list[StorageTypeDict]
    Place: VectorDict[float]
    Id: str


class StorageTypeDict(TypedDict):
    Part: str
    Add: int
    Remove: int
    Requires: NotRequired[list[str]]


ModelsDict = dict[str, StationModelDict]
