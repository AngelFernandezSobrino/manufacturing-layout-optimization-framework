from __future__ import annotations

from dataclasses import dataclass
import json
from math import sqrt
from typing import Dict, Generic, List, NotRequired, Optional, TypeVar, TypedDict


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


class StationModel:

    def __init__(self, name: str, station_model_dict: StationModelDict) -> None:
        self.name: str = name
        try:
            self.storage = [Storage(s) for s in station_model_dict["Storage"]]
        except:
            self.storage = None

        try:
            self.transport = Transport(station_model_dict["Transport"])
        except:
            self.transport = None

        try:
            self.activities = station_model_dict["Activities"]
        except:
            self.activities = None

    def __str__(self) -> str:
        return f"{self.name}"

    def toJSON(self):
        return json.dumps(self)


PlantGridType = List[List[StationModel | None]]


class Storage:

    def __init__(
        self,
        storage_dict: StorageDict,
    ) -> None:
        self.type: List[str] = storage_dict["Type"]
        self.place: Vector[float] = Vector(
            storage_dict["Place"]["X"], storage_dict["Place"]["Y"]
        )
        self.add: int = storage_dict["Add"]
        self.remove: int = storage_dict["Remove"]
        self.requires: List[str]


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
        self.size = Vector(stations_dict["Size"]["X"], stations_dict["Size"]["Y"])
        self.models: Dict[str, StationModel] = {
            k: StationModel(k, v) for k, v in stations_dict["Models"].items()
        }


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
    Size: VectorDict[float]
    Models: Dict[str, StationModelDict]


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


class StorageDict(TypedDict):
    Type: List[str]
    Place: VectorDict[float]
    Add: int
    Remove: int


ModelsDict = Dict[str, StationModelDict]
