"""Inspect maps with the existing Fly-in routing and simulation code."""

import argparse
from pathlib import Path
import sys

from algorithms import dijkstra
from map_parser import MapParseError, parse_map
from models import Graph
from planning import initialize_positions, run_route


def _print_details(graph: Graph) -> None:
    print("Zones:")
    for name, zone in sorted(graph.zones.items()):
        print(
            f"  {name}: ({zone.x}, {zone.y}), zone={zone.zone_type.value}, "
            f"max_drones={zone.max_drones}, color={zone.color or '-'}"
        )
    links = {
        (*sorted((link.origin.name, link.destination.name)), link.capacity)
        for connections in graph.connections.values()
        for link in connections
    }
    print("Connections (bidirectional):")
    for origin, destination, capacity in sorted(links):
        print(f"  {origin}-{destination}: max_link_capacity={capacity}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_path", type=Path, help="path to a Fly-in map")
    operations = parser.add_mutually_exclusive_group()
    operations.add_argument(
        "--info-only", action="store_true",
        help="show graph information without running Dijkstra",
    )
    operations.add_argument(
        "--simulate", action="store_true",
        help=(
            "run the existing greedy planner and simulator "
            "on the Dijkstra route"
        ),
    )
    parser.add_argument(
        "--details", action="store_true",
        help="list all zone and link attributes",
    )
    args = parser.parse_args(argv)

    try:
        graph, nb_drones, start, end = parse_map(args.map_path)
    except MapParseError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    nb_connections = sum(
        len(links) for links in graph.connections.values()
    ) // 2
    print(f"Map: {args.map_path}")
    print(f"Zones: {len(graph.zones)}")
    print(f"Connections: {nb_connections} (bidirectional)")
    print(f"Drones: {nb_drones}")
    print(f"START: {start}")
    print(f"END: {end}")
    if args.details:
        _print_details(graph)
    if args.info_only:
        return 0

    route = dijkstra(graph, start, end)
    if not route:
        print(f"error: no route from {start} to {end}", file=sys.stderr)
        return 1
    print(f"Dijkstra route (single drone): {' -> '.join(route)}")
    cost = sum(graph.zones[name].movement_cost() for name in route[1:])
    print(f"Route travel time (without congestion): {cost} turn(s)")

    if args.simulate:
        print("Simulation on this route using the existing greedy planner.")
        print("This operation does not optimize routes for multiple drones.")
        positions = initialize_positions(nb_drones, start)
        try:
            history = run_route(graph, positions, route, start, end)
        except RuntimeError as error:
            if str(error) != "Simulation stalled":
                raise
            print(f"error: route simulation stalled: {error}", file=sys.stderr)
            return 1
        for turn, state in enumerate(history):
            drones = []
            for drone_id, position in sorted(state.items()):
                if isinstance(position, tuple):
                    origin, destination = position
                    location = f"{origin}->{destination} (in transit)"
                else:
                    location = position
                drones.append(f"D{drone_id}={location}")
            print(f"Turn {turn}: {' '.join(drones)}")
        print(f"Simulation turns: {len(history) - 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
