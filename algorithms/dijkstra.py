from models import Graph, ZoneType


def dijkstra(graph: Graph, start: str, end: str) -> list[str]:
    """Find a route with the fewest movement turns.

    Skip blocked zones and charge two turns to enter a restricted zone
    and one for any other traversable zone. Among routes with equal
    movement cost, prefer those entering more priority zones.
    The search ignores drone occupancy and connection capacity.

    Args:
        graph: Network of zones and undirected connections.
        start: Name of the departure zone.
        end: Name of the destination zone.

    Returns:
        Zone names along the route, including both endpoints. Return an
        empty list if either endpoint is blocked or no route exists.
        Return a single name if both endpoints are the same open zone.

    Raises:
        ValueError: Either endpoint is absent from the graph.
    """
    if start not in graph.zones or end not in graph.zones:
        raise ValueError("Start or end zone does not exist")

    if (graph.zones[start].zone_type == ZoneType.BLOCKED
            or graph.zones[end].zone_type == ZoneType.BLOCKED):
        return []

    distances: dict[str, float] = {
        name: float("inf") for name in graph.zones
    }

    priority_counts: dict[str, int] = {
        name: 0 for name in graph.zones
    }

    previous: dict[str, str | None] = {
        name: None for name in graph.zones
    }

    distances[start] = 0

    unvisited: set[str] = set(graph.zones)

    while unvisited:
        current = min(
            unvisited,
            key=lambda name: (distances[name],
                              -priority_counts,
                              name)
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

            new_priority_count = priority_counts[current]

            if neighbor.zone_type == ZoneType.PRIORITY:
                new_priority_count += 1

            if (
                new_distance < distances[neighbor.name]
                or (
                    new_distance == distances[neighbor.name]
                    and new_priority_count > priority_counts[neighbor.name]
                )
            ):
                distances[neighbor.name] = new_distance
                priority_counts[neighbor.name] = new_priority_count
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
