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


class ProcessGraphNode(DirectedGraphNode, Generic[DirectedGraphEdgeInterface]):
    """
    Representation of each node of the graph, it contains the station and all the directed edges to the other stations.

    """

    def __init__(self, station: model.StationModel) -> None:
        self.id: str = station.name
        self.edges: List[DirectedGraphEdgeInterface] = []

        self.station: model.StationModel = station
        self.position: model.Vector

    def reset_position(self) -> None:
        self.position = model.Vector(0, 0)

    def __str__(self) -> str:
        return f"Station: {self.station}"


class ProcessGraphEdge(DirectedGraphEdge):
    """
    Representation of directed  edges of the graph, it contains the part associated with that edge and the destination node. This edge represents a transport capability between two stations in one direction. Any edge has to go from a storage station to a transport station or from a transport station to a storage station.

    """

    def __init__(
        self, part: Any, origin: ProcessGraphNode, destiny: ProcessGraphNode
    ) -> None:
        self.id: str = f"{part}"
        self.destiny: ProcessGraphNode = destiny
        self.origin: ProcessGraphNode = origin
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


class ProcessGraphEdgeWithTransport(DirectedGraphEdge):
    """
    Representation of directed  edges of the graph, it contains the part associated with that edge and the destination node. This edge represents a transport capability between two stations in one direction. EdgeWithTransport is a special case of Edge, it has a transport station associated. Any edge has to go from a storage station to another storage station, but it has to go through a transport station. The transport station that is used is stored in the transport_station attribute.o

    """

    def __init__(self, part: Any, transport: model.StationModel) -> None:
        self.id: str = f"{part} to {transport.name}"
        self.node: ProcessGraphNode

        self.part = part
        self.transport: model.StationModel

    def __str__(self) -> str:
        return f"Part: {self.part}, Destination: {self.node}, Transport station: {self.transport}"

    def __eq__(self, __other: Any) -> bool:

        if (
            self.part == __other.part
            and self.node == __other.node
            and self.transport == __other.transport
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