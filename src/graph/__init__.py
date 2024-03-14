from __future__ import annotations
from enum import Enum

# We need a class to represent the edges of the graph, it would contain the part and the destination node

import model as model
from typing import Any, Generic, List, TypeVar

# We need a class to represent the each node of the graph, it would contain the station and all the directed edges to the other stations
# Edges may have a part associated


DirectedGraphNodeInterface = TypeVar(
    "DirectedGraphNodeInterface", bound="DirectedGraphNode"
)
DirectedGraphEdgeInterface = TypeVar(
    "DirectedGraphEdgeInterface", bound="DirectedGraphEdge"
)


class DirectedGraphNode(Generic[DirectedGraphEdgeInterface]):

    def __init__(self) -> None:
        self.id: str
        self.edges: List[DirectedGraphEdgeInterface]


class DirectedGraphEdge(Generic[DirectedGraphNodeInterface]):
    def __init__(self) -> None:
        self.id: str
        self.origin: DirectedGraphNodeInterface
        self.destiny: DirectedGraphNodeInterface


class StationNode(DirectedGraphNode):
    """
    Representation of each node of the graph, it contains the station and all the directed edges to the other stations.

    """

    def __init__(self, station: model.StationModel) -> None:
        self.id: str = station.name
        self.model: model.StationModel = station

        self.storage_nodes: List[StorageNode] = []

        self.edges: List[RoutingGraphEdge] = []

        self.position: model.Vector[float]

        self.generate_storage_nodes()

    def generate_storage_nodes(self) -> None:
        if self.model.storages is None:
            return

        for storage in self.model.storages:
            storage_node = StorageNode(storage, self)
            storage_node.relative_position = storage.position
            self.storage_nodes.append(storage_node)

    def reset_position(self) -> None:
        self.position = model.Vector(0, 0)

    def __str__(self) -> str:
        return f"{self.id}"

    def __repr__(self) -> str:
        return self.__str__()


class StorageNode(DirectedGraphNode):
    """
    Representation of each node of the graph, it contains the station and all the directed edges to the other stations.

    """

    def __init__(self, storage: model.Storage, station: StationNode) -> None:
        self.id: str = f"{station.model.name}-{storage.type}-{storage.position}"
        self.model: model.Storage = storage

        self.parent_station: StationNode = station

        self.edges: List[RoutingGraphEdge] = []
        self.pathing_edges: List[PathEdge] = []

        self.relative_position: model.Vector[float] = model.Vector(
            storage.position.x, storage.position.y
        )

    def absolute_position(self) -> model.Vector[float]:
        return self.parent_station.position + self.relative_position

    def __str__(self) -> str:
        return f"{self.id}"

    def __repr__(self) -> str:
        return self.__str__()


class RoutingGraphEdge(DirectedGraphEdge):
    """
    Representation of directed  edges of the graph, it contains the part associated with that edge and the destination node. This edge represents a transport capability between two stations in one direction. Any edge has to go from a storage station to a transport station or from a transport station to a storage station.

    """

    class Direction(Enum):
        INPUT = 1  # Input to storage, from transport to storage
        OUTPUT = 2  # Output from storage, from storage to transport

    def __init__(
        self,
        part: str,
        transport: StationNode,
        storage: StorageNode,
        direction: Direction,
    ) -> None:
        self.id: str = f"{part}"

        self.transport = transport
        self.storage = storage
        self.direction = direction
        self.origin = None
        self.destiny = None
        self.part = part

    def __str__(self) -> str:
        moving_symbol = (
            "->" if self.direction == RoutingGraphEdge.Direction.INPUT else "<-"
        )
        return f"{self.transport} {moving_symbol} {self.part} {moving_symbol} {self.storage}"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, __other: Any) -> bool:
        if not isinstance(__other, RoutingGraphEdge):
            raise NotImplemented

        if (
            self.id == __other.id
            and self.transport == __other.transport
            and self.storage == __other.storage
        ):
            return True
        else:
            return False


class PathEdge(DirectedGraphEdge):

    def __init__(self, part: str, origin: StorageNode, destiny: StorageNode) -> None:

        self.id = f"{part}"

        self.origin = origin
        self.destiny = destiny

        self.part = part

    def __str__(self) -> str:
        return f"{self.origin} -> {self.part} -> {self.destiny}"

    def __repr__(self) -> str:
        return self.__str__()


class TreeNode:
    """
    Representation of each node of the graph. This node is used in the tree of configurations. It contains the station and the position of the station in the plant. It also contains the previous node and the next nodes. The next nodes are the subsequent configuration decisions made from the current node.

    """

    def __init__(
        self, station: model.StationModel, position: model.Vector[int], previous_node
    ) -> None:

        self.next: List[TreeNode] | None = None
        self.previous: TreeNode | None = previous_node

        self.station: model.StationModel = station
        self.position: model.Vector[int] = position

    def __str__(self) -> str:
        return f"{self.station} {self.position}"

    def count_leaves(self) -> int:
        if self.next is None:
            return 1

        count = 0

        for node in self.next:
            count += node.count_leaves()

        return count
