from graph import Graph


def dijkstra(graph: Graph, start: str, end: str) -> list[str]:
    if start not in graph.zones or end not in graph.zones:
        raise ValueError("Start or end zone does not exist")

    distances: dict[str, float] = {
        name: float("inf") for name in graph.zones
    }

    previous: dict[str, str | None] = {
        name: None for name in graph.zones
    }

    distances[start] = 0
    unvisited: set[str] = set(graph.zones)

    while unvisited:
    current = min(unvisited, key=lambda name: distances[name])
    unvisited.remove(current)

    raise NotImplementedError("Dijkstra todavía no está terminado")