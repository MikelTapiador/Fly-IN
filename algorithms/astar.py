

Position = str | tuple[str, str]

Occupancy = tuple[Position, int]

State = frozenset[Occupancy]


def build_state(positions: dict[int, Position]) -> State:
    occupancy: dict[Position, int] = {}

    for position in positions.values():
        if position in occupancy:
            occupancy[position] += 1
        else:
            occupancy[position] = 1

    return frozenset(occupancy.items())
