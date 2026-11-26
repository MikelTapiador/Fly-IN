from models import Graph
from .simulator import simulate_turn


def run_schedule(
    graph: Graph,
    positions: dict[int, str | tuple[str, str]],
    schedule: list[dict[int, str]],
    start: str,
    end: str
) -> list[dict[int, str | tuple[str, str]]]:
    """Replay a sequence of scheduled turns.

    Args:
        graph: Network used to validate movements.
        positions: Initial positions by drone ID. A zone name denotes
            a settled drone, and an endpoint pair denotes transit.
        schedule: Requested destination assignments for each turn.
        start: Name of the start zone, exempt from occupancy checks.
        end: Name of the terminal zone, exempt from occupancy checks.

    Returns:
        Position snapshots in turn order, starting with a copy of the
        initial state. An empty schedule yields only that initial copy.

    Raises:
        ValueError: The simulator rejects a scheduled turn.
        KeyError: A resulting occupied zone other than start or end is
            missing from the graph's zone registry.
    """

    history = [positions.copy()]

    for moves in schedule:
        positions = simulate_turn(graph, positions, moves, start, end)
        history.append(positions.copy())

    return history


def get_candidate_moves(
    graph: Graph,
    drone_id: int,
    position: str | tuple[str, str],
    end: str
) -> list[dict[int, str]]:
    """Enumerate possible assignments for one drone before validation.

    Args:
        graph: Network whose connections supply adjacent destinations.
        drone_id: Drone to assign a destination to.
        position: Current zone name or a pair of transit endpoints.
        end: Name of the terminal zone.

    Returns:
        An empty assignment first, followed by one assignment per
        adjacent zone. Return only the empty assignment if the drone
        is in transit, is at the end, or has no listed connections.
    """

    candidates: list[dict[int, str]] = [{}]

    if isinstance(position, tuple) or position == end:
        return candidates

    for connection in graph.connections.get(position, []):
        if connection.origin.name == position:
            destination = connection.destination.name
        else:
            destination = connection.origin.name

        candidates.append({drone_id: destination})

    return candidates


def get_valid_transitions(
    graph: Graph,
    drone_id: int,
    positions: dict[int, str | tuple[str, str]],
    reserved_moves: dict[int, str],
    start: str,
    end: str
) -> list[tuple[dict[int, str], str | tuple[str, str]]]:
    """Evaluate one drone's candidate moves alongside reserved moves.

    Simulate each merged assignment and discard turns rejected with
    ValueError. A nonempty candidate overrides a reservation for the
    same drone. An empty candidate leaves all reservations in place.

    Args:
        graph: Network used to validate each turn.
        drone_id: ID of the drone whose candidates are evaluated.
        positions: Current positions by drone ID as zone names or pairs
            of transit endpoints.
        reserved_moves: Destination assignments to include in each trial.
        start: Name of the start zone, exempt from occupancy checks.
        end: Name of the terminal zone, exempt from occupancy checks.

    Returns:
        Pairs of the candidate assignment and the drone's resulting
        position. Return an empty list if every trial is rejected.

    Raises:
        KeyError: The drone is absent from positions, or a resulting
            occupied zone is absent from the graph's zone registry.
    """

    transitions = []

    candidates = get_candidate_moves(
        graph, drone_id, positions[drone_id], end
    )

    for candidate in candidates:
        moves = reserved_moves.copy()
        moves.update(candidate)

        try:
            new_positions = simulate_turn(
                graph, positions, moves, start, end
            )
        except ValueError:
            continue

        transitions.append((candidate, new_positions[drone_id]))

    return transitions
