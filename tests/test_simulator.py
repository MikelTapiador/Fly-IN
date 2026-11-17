
from models import Graph, Zone, ZoneType
from planning.simulator import simulate_turn

graph = Graph()

graph.add_zone(Zone("START", 0, 0))
graph.add_zone(Zone("A", 1, 0))
graph.add_zone(Zone("END", 2, 0))

graph.add_connection("START", "A")
graph.add_connection("A", "END")


positions = {
    1: "A",
    2: "START"
}

moves = {
    1: "END",
    2: "A"
}

result = simulate_turn(
    graph,
    positions,
    moves,
    "START",
    "END"
)

assert result == {
    1: "END",
    2: "A"
}

print("Test passed")


positions = {1: "START", 2: "START"}
moves = {1: "A", 2: "A"}

try:
    simulate_turn(graph, positions, moves, "START", "END")
except ValueError as error:
    print("Test passed:", error)
else:
    raise AssertionError("Expected a ValueError")

graph2 = Graph()

graph2.add_zone(Zone("START", 0, 0))
graph2.add_zone(Zone("A", 1, 0, max_drones=1))
graph2.add_zone(Zone("END", 2, 0))

graph2.add_connection("START", "A", capacity=2)
graph2.add_connection("A", "END")

positions = {1: "START", 2: "START"}
moves = {1: "A", 2: "A"}

try:
    simulate_turn(graph2, positions, moves, "START", "END")
except ValueError as error:
    assert str(error) == "Zone capacity exceeded"
    print("Zone capacity test passed")
else:
    raise AssertionError("Expected zone capacity error")


# Test restricted zone movement

restricted_graph = Graph()

restricted_graph.add_zone(Zone("START", 0, 0))
restricted_graph.add_zone(
    Zone("R", 1, 0, zone_type=ZoneType.RESTRICTED)
)
restricted_graph.add_zone(Zone("END", 2, 0))

restricted_graph.add_connection("START", "R")
restricted_graph.add_connection("R", "END")

positions = {1: "START"}

# First turn: drone enters the connection
positions = simulate_turn(
    restricted_graph,
    positions,
    {1: "R"},
    "START",
    "END"
)

assert positions == {1: ("START", "R")}

# Second turn: drone must arrive at R
positions = simulate_turn(
    restricted_graph,
    positions,
    {},
    "START",
    "END"
)

assert positions == {1: "R"}

print("Restricted movement test passed")


# Test connection occupied by a drone in transit

positions = {
    1: ("START", "R"),
    2: "START"
}

moves = {
    2: "R"
}

try:
    simulate_turn(
        restricted_graph,
        positions,
        moves,
        "START",
        "END"
    )
except ValueError as error:
    assert str(error) == "Connection capacity exceeded"
    print("Transit capacity test passed")
else:
    raise AssertionError("Expected connection capacity error")


# Test simultaneous arrival and departure

positions = {
    1: ("START", "R"),
    2: "R"
}

moves = {
    2: "END"
}

result = simulate_turn(
    restricted_graph,
    positions,
    moves,
    "START",
    "END"
)

assert result == {
    1: "R",
    2: "END"
}

print("Simultaneous arrival test passed")
