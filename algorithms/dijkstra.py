from models.graph import Graph
from models.zones_and_connections import ZoneType


def dijkstra(graph: Graph, start: str, end: str) -> list[str]:
    # 1. Validate start and end zones
    if start not in graph.zones or end not in graph.zones:
        raise ValueError("Start or end zone does not exist")

    if (graph.zones[start].zone_type == ZoneType.BLOCKED
            or graph.zones[end].zone_type == ZoneType.BLOCKED):
        return []

    # 2. Initialize distances
    distances: dict[str, float] = {
        name: float("inf") for name in graph.zones
    }

    # 3. Initialize predecessors
    previous: dict[str, str | None] = {
        name: None for name in graph.zones
    }

    distances[start] = 0

    # 4. Initialize unvisited zones
    unvisited: set[str] = set(graph.zones)

    while unvisited:
        # 5. Select the zone with the shortest known distance
        current = min(
            unvisited,
            key=lambda name: (distances[name], name)
        )

        if distances[current] == float("inf"):
            break

        unvisited.remove(current)

        if current == end:
            break

        # 6. Explore neighboring zones
        for neighbor in graph.get_neighbors(current):
            if neighbor.name not in unvisited:
                continue

            if neighbor.zone_type == ZoneType.BLOCKED:
                continue

            # 7. Calculate movement cost
            cost = (
                2 if neighbor.zone_type == ZoneType.RESTRICTED
                else 1
            )

            new_distance = distances[current] + cost

            # 8. Update distance if a shorter path is found
            if new_distance < distances[neighbor.name]:
                distances[neighbor.name] = new_distance
                previous[neighbor.name] = current

    # 9. Check whether the destination is reachable
    if distances[end] == float("inf"):
        return []

    # 10. Reconstruct the shortest path
    path: list[str] = []
    current_node: str | None = end

    while current_node is not None:
        path.append(current_node)
        current_node = previous[current_node]

    path.reverse()

    return path
