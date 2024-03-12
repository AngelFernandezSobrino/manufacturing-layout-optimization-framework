from __future__ import annotations

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
        self.node: DirectedGraphNodeInterface


class StationNode(DirectedGraphNode):
    """
    Representation of each node of the graph, it contains the station and all the directed edges to the other stations.

    """

    def __init__(self, station: model.StationModel) -> None:
        self.id: str = station.name
        del self.edges

        self.station: model.StationModel = station
        self.storage_nodes: List[StorageNode] = []
        self.position: model.Vector

    def generate_storage_nodes(self) -> None:
        if self.station.storages is None:
            return

        for storage in self.station.storages:
            storage_node = StorageNode(storage)
            storage_node.relative_position = storage.position
            self.storage_nodes.append(storage_node)

    def reset_position(self) -> None:
        self.position = model.Vector(0, 0)

    def __str__(self) -> str:
        return f"Station: {self.station}"


class StorageNode(DirectedGraphNode):
    """
    Representation of each node of the graph, it contains the station and all the directed edges to the other stations.

    """

    def __init__(self, storage: model.Storage, station: model.StationModel) -> None:
        self.id: str = f"{station.name} - {storage.type} - {storage.position}"
        self.edges: List[ProcessGraphEdge] = []
        self.storage: model.Storage = storage
        self.parent_station: StationNode = station
        self.relative_position: model.Vector

    def absolute_position(self) -> model.Vector:
        return self.station.position + self.relative_position

    def __str__(self) -> str:
        return f"Station: {self.station}"


class ProcessGraphEdge(DirectedGraphEdge):
    """
    Representation of directed  edges of the graph, it contains the part associated with that edge and the destination node. This edge represents a transport capability between two stations in one direction. Any edge has to go from a storage station to a transport station or from a transport station to a storage station.

    """

    def __init__(self, part: Any, origin: StationNode, destiny: StationNode) -> None:
        self.id: str = f"{part}"
        self.destiny: StationNode = destiny
        self.origin: StationNode = origin
        self.part = part

    def __str__(self) -> str:
        return f"Part: {self.part}, Origin: {self.origin} Destiny: {self.destiny}"

    def __eq__(self, __other: Any) -> bool:
        if not isinstance(__other, ProcessGraphEdge):
            raise NotImplemented

        if (
            self.id == __other.id
            and self.origin == __other.origin
            and self.destiny == __other.destiny
        ):
            return True
        else:
            return False


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
