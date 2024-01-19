# We need a class to represent the edges of the graph, it would contain the part and the destination node

from dataclasses import dataclass
import model
from typing import Any, List


@dataclass
class Edge:
    part: str
    destination: Any

    def __str__(self) -> str:
        return f"Part: {self.part}, Destination: {self.destination}"

    def __eq__(self, __value) -> bool:
        if self.part == __value.part and self.destination == __value.destination:
            return True
        else:
            return False


@dataclass
class EdgeWithTransport:
    part: str
    destination: Any
    transport_station: Any

    def __str__(self) -> str:
        return f"Part: {self.part}, Destination: {self.destination}, Transport station: {self.transport_station}"

    def __eq__(self, __value) -> bool:
        if (
            self.part == __value.part
            and self.destination == __value.destination
            and self.transport_station == __value.transport_station
        ):
            return True
        else:
            return False


# We need a class to represent the each node of the graph, it would contain the station and all the directed edges to the other stations
# Edges may have a part associated


@dataclass
class Node:
    station: model.StationModel
    outgoing_edges: List[Edge | EdgeWithTransport]

    def __str__(self) -> str:
        return f"Station: {self.station}"
