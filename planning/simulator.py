from models import Graph, ZoneType


def initialize_positions(
    nb_drones: int,
    start: str
) -> dict[int, str]:
    """Place the fleet in the start zone.

    Args:
        nb_drones: Number of drones to place.
        start: Zone name assigned to each drone.

    Returns:
        Zone names indexed by consecutive drone IDs starting at one.
        A nonpositive count yields an empty dictionary.
    """
    return {
        drone_id: start
        for drone_id in range(1, nb_drones + 1)
    }


def get_occupancy(
    positions: dict[int, str | tuple[str, str]]
) -> dict[str, int]:
    """Count drones settled in zones.

    Args:
        positions: Positions by drone ID as zone names or pairs of
            transit endpoints.

    Returns:
        Counts indexed by occupied zone name. Drones in transit and
        unoccupied zones are omitted.
    """

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
    """Apply one turn of simultaneous drone movements.

    Complete existing transits automatically and record new entries
    into restricted zones as endpoint pairs. Drones without a move or
    active transit stay in place. Link usage includes trips that start
    or finish in the turn and is shared by both directions. Check
    zone occupancy after applying all moves, exempting start and end.

    Args:
        graph: Network defining adjacency, zone types, and capacities.
        positions: Current positions by drone ID. Transit positions
            contain the origin and destination zone names.
        moves: Requested destination zone names by drone ID.
        start: Name of the start zone.
        end: Name of the terminal zone. Drones there cannot move out.

    Returns:
        A new position dictionary with zone names for settled drones
        and endpoint pairs for drones still in transit.

    Raises:
        ValueError: A requested move is invalid or exceeds link
            capacity, or the resulting zone occupancy exceeds capacity.
        KeyError: A resulting occupied zone other than start or end is
            missing from the graph's zone registry.
    """

    new_positions = positions.copy()
    link_usage: dict[tuple[str, str], int] = {}
    origin: str | tuple[str, str]

    for drone_id, position in positions.items():
        if isinstance(position, tuple):

            if drone_id in moves:
                raise ValueError("Drone already in transit")

            origin, destination = position

            link = (min(origin, destination), max(origin, destination))
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

        link = (min(origin, destination), max(origin, destination))
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
