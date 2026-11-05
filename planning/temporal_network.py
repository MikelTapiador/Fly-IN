from models.graph import Graph

TemporalNode = tuple[str, int, str]
TemporalEdge = tuple[TemporalNode, TemporalNode, int]

def build_temporal_nodes(
    graph: Graph,
    turns: int
) -> set[TemporalNode]:

    nodes: set[TemporalNode] = set()

    for name in graph.zones:
        for turn in range(len(turns + 1)):
            nodes.add((name, turn, "in"))
            nodes.add((name, turn, "out"))

    return nodes

def build_occupancy_edges(
    graph: Graph,
    turns: int
) -> list[TemporalEdge]:

    edges: list[TemporalEdge] = []

    for name, zone in graph.zones.items():
        for turn in range(turns + 1):
            origin = (name, turn, "in")
            destination = (name, turn, "out")

            edges.append((origin, destination, zone.max_drones))

    return edges

def build_movement_edges(
    graph: Graph,
    turns: int
) -> list[TemporalEdge]:

    edges: list[TemporalEdge] = []

    for name, connections in graph.connections.items():
        for connection in connections:

            if connection.origin.name == name:
                neighbor = connection.destination
            else:
                neighbor = connection.origin

            for turn in range(turns):
                origin = (name, turn, "out")
                destination = (neighbor.name, turn + 1, "in")

                edges.append((origin, destination, connection.capacity))

    return edges

def build_waiting_edges(
    graph: Graph,
    turns: int
) -> list[TemporalEdge]:

    edges: list[TemporalEdge] = []

    for name, zone in graph.zones.items():
        for turn in range(turns):
            origin = (name, turn, "out")
            destination = (name, turn + 1, "in")

            edges.append((origin, destination, zone.max_drones))

    return edges