"""Run a fixed drone schedule for the map supplied on the command line.

Print each position snapshot, the number of turns, and the valid
transitions for two sample states. The schedule uses two drone IDs
and assumes the map contains the sample waypoints.
"""

import sys
from map_parser import parse_map
from algorithms import dijkstra
from planning import initialize_positions, run_schedule, get_valid_transitions

if len(sys.argv) != 2:
    print("Usage: python3 main.py <map_file>", file=sys.stderr)
    sys.exit(1)

graph, nb_drones, start, end = parse_map(sys.argv[1])

initial_positions = initialize_positions(nb_drones, start)

schedule = [
    {1: "waypoint1"},
    {1: "waypoint2", 2: "waypoint1"},
    {1: end, 2: "waypoint2"},
    {2: end}
]

simulation = run_schedule(graph, initial_positions, schedule, start, end)

for turn, position in enumerate(simulation):
    print(f"Turno {turn}: {position}")

print(f"Total turns: {len(simulation) - 1}")

positions = {1: start, 2: start}
reserved_moves = {1: "waypoint1"}

print(get_valid_transitions(
    graph, 2, positions, reserved_moves, start, end
))

positions = {1: "waypoint1", 2: start}
reserved_moves = {1: "waypoint2"}

print(get_valid_transitions(
    graph, 2, positions, reserved_moves, start, end
))