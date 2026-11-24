import sys
from map_parser import parse_map
from algorithms import dijkstra
from planning import initialize_positions
from planning import run_route
from algorithms import build_state

if len(sys.argv) != 2:
    print("Usage: python3 main.py <map_file>", file=sys.stderr)
    sys.exit(1)

graph, nb_drones, start, end = parse_map(sys.argv[1])

route = dijkstra(graph, start, end)

print(route)

initial_positions = initialize_positions(nb_drones, start)

simulation = run_route(graph, initial_positions, route, start, end)

for turn, position in enumerate(simulation):
    # print(f"Turno{turn}: {position}")
    print(build_state(position))

print(f"Total turns: {len(simulation) - 1}")


