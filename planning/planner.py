
from models import Graph, ZoneType
from planning.simulator import simulate_turn


def plan_turn(
    graph: Graph,
    positions: dict[int, str | tuple[str, str]],
    route: list[str],
    start: str,
    end: str
) -> dict[int, str]:

    moves: dict[int, str] = {}

    # Process zones from destination to origin.
    for index in range(len(route) - 2, -1, -1):
        origin = route[index]
        destination = route[index + 1]

        for drone_id, position in positions.items():
            if position != origin:
                continue

            candidate = moves.copy()
            candidate[drone_id] = destination

            if (
                graph.zones[destination].zone_type == ZoneType.RESTRICTED
                and destination not in (start, end)
            ):
                arrivals = sum(
                    1 for target in candidate.values()
                    if target == destination
                )

                if arrivals > graph.zones[destination].max_drones:
                    continue

            try:
                simulate_turn(graph, positions, candidate, start, end)
            except ValueError:
                continue

            moves = candidate

    return moves


def run_route(
    graph: Graph,
    positions: dict[int, str | tuple[str, str]],
    route: list[str],
    start: str,
    end: str
) -> list[dict[int, str | tuple[str, str]]]:

    history = [positions.copy()]

    while not all(pos == end for pos in positions.values()):

        moves = plan_turn(graph, positions, route, start, end)

        new_positions = simulate_turn(
            graph, positions, moves, start, end
        )

        if new_positions == positions:
            raise RuntimeError("Simulation stalled")

        positions = new_positions
        history.append(positions.copy())

    return history
