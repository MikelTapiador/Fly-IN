from models import Graph, ZoneType


def initialize_positions(
    nb_drones: int,
    start: str
) -> dict[int, str]:
    return {
        drone_id: start
        for drone_id in range(1, nb_drones + 1)
    }


def get_occupancy(
    positions: dict[int, str | tuple[str, str]]
) -> dict[str, int]:

    occupancy: dict[str, int] = {}

    for position in positions.values():
        if isinstance(position, str):
            occupancy[position] = occupancy.get(position, 0) + 1

    return occupancy


def simulate_turn(
    graph: Graph,
    positions: dict[int, str | tuple[str, str]],
    moves: dict[int, str],
    start: str,
    end: str
) -> dict[int, str | tuple[str, str]]:

    new_positions = positions.copy()
    link_usage: dict[tuple[str, str], int] = {}

    for drone_id, position in positions.items():
        if isinstance(position, tuple):

            if drone_id in moves:
                raise ValueError("Drone already in transit")

            origin, destination = position

            link = tuple(sorted((origin, destination)))
            link_usage[link] = link_usage.get(link, 0) + 1

            new_positions[drone_id] = destination

    for drone_id, destination in moves.items():
        if drone_id not in positions:
            raise ValueError("Unknown drone")

        origin = positions[drone_id]

        if isinstance(origin, tuple):
            raise ValueError("Drone already in transit")

        if origin == end or destination == origin:
            raise ValueError("Invalid movement")

        if destination not in graph.zones:
            raise ValueError("Unknown destination")

        zone = graph.zones[destination]

        if zone.zone_type == ZoneType.BLOCKED:
            raise ValueError("Blocked zone")

        connection = next(
            (
                c for c in graph.connections.get(origin, [])
                if destination in (c.origin.name, c.destination.name)
            ),
            None
        )

        if connection is None:
            raise ValueError("Zones are not connected")

        link = tuple(sorted((origin, destination)))
        link_usage[link] = link_usage.get(link, 0) + 1

        if link_usage[link] > connection.capacity:
            raise ValueError("Connection capacity exceeded")

        if zone.zone_type == ZoneType.RESTRICTED:
            new_positions[drone_id] = (origin, destination)
        else:
            new_positions[drone_id] = destination

    occupancy = get_occupancy(new_positions)

    for name, count in occupancy.items():
        if name not in (start, end):
            if count > graph.zones[name].max_drones:
                raise ValueError("Zone capacity exceeded")

    return new_positions
