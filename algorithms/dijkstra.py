from models import Graph, ZoneType


def dijkstra(graph: Graph, start: str, end: str) -> list[str]:
    if start not in graph.zones or end not in graph.zones:
        raise ValueError("Start or end zone does not exist")

    if (graph.zones[start].zone_type == ZoneType.BLOCKED
            or graph.zones[end].zone_type == ZoneType.BLOCKED):
        return []

    distances: dict[str, float] = {
        name: float("inf") for name in graph.zones
    }

    previous: dict[str, str | None] = {
        name: None for name in graph.zones
    }

    distances[start] = 0

    unvisited: set[str] = set(graph.zones)

    while unvisited:
        current = min(
            unvisited,
            key=lambda name: (distances[name], name)
        )

        if distances[current] == float("inf"):
            break

        unvisited.remove(current)

        if current == end:
            break

        for neighbor in graph.get_neighbors(current):
            if neighbor.name not in unvisited:
                continue

            if neighbor.zone_type == ZoneType.BLOCKED:
                continue

            cost = (
                2 if neighbor.zone_type == ZoneType.RESTRICTED
                else 1
            )

            new_distance = distances[current] + cost

            if new_distance < distances[neighbor.name]:
                distances[neighbor.name] = new_distance
                previous[neighbor.name] = current

    if distances[end] == float("inf"):
        return []

    path: list[str] = []
    current_node: str | None = end

    while current_node is not None:
        path.append(current_node)
        current_node = previous[current_node]

    path.reverse()

    return path
