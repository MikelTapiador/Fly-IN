
from models import Graph, Zone
from planning import plan_turn, simulate_turn


graph = Graph()

graph.add_zone(Zone("START", 0, 0))
graph.add_zone(Zone("A", 1, 0))
graph.add_zone(Zone("END", 2, 0))

graph.add_connection("START", "A")
graph.add_connection("A", "END")

route = ["START", "A", "END"]
positions = {1: "START", 2: "START"}

for turn in range(1, 4):
    moves = plan_turn(
        graph, positions, route, "START", "END"
    )

    positions = simulate_turn(
        graph, positions, moves, "START", "END"
    )

    print(f"Turn {turn}: {moves}")

assert positions == {1: "END", 2: "END"}

print("Planner test passed")
