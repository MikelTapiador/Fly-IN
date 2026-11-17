
from models import Graph, Zone, ZoneType
from planning.planner import plan_turn
from planning.simulator import simulate_turn


graph = Graph()

graph.add_zone(Zone("START", 0, 0))
graph.add_zone(Zone("R", 1, 0, ZoneType.RESTRICTED))
graph.add_zone(Zone("END", 2, 0))

graph.add_connection("START", "R")
graph.add_connection("R", "END")

route = ["START", "R", "END"]

positions = {
    1: "START",
    2: "START",
    3: "START"
}

turn = 0

from planning.planner import run_route

positions = {1: "START", 2: "START", 3: "START"}

history = run_route(
    graph, positions, route, "START", "END"
)

assert len(history) - 1 == 7
assert history[-1] == {
    1: "END",
    2: "END",
    3: "END"
}

print("Run route test passed")


# Test simultaneous arrivals at a restricted zone

capacity_graph = Graph()

capacity_graph.add_zone(Zone("START", 0, 0))
capacity_graph.add_zone(
    Zone("R", 1, 0, ZoneType.RESTRICTED, max_drones=1)
)
capacity_graph.add_zone(Zone("END", 2, 0))

capacity_graph.add_connection("START", "R", capacity=2)
capacity_graph.add_connection("R", "END")

positions = {1: "START", 2: "START"}
route = ["START", "R", "END"]

history = run_route(
    capacity_graph, positions, route, "START", "END"
)

assert history[-1] == {1: "END", 2: "END"}

print("Restricted arrival capacity test passed")
