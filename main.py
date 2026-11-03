from graph import Graph
from models import Zone, ZoneType
from pathfinding import dijkstra


def main() -> None:
    graph = Graph()

    graph.add_zone(Zone("A", 0, 0))
    graph.add_zone(Zone("B", 1, 1, ZoneType.RESTRICTED))
    graph.add_zone(Zone("C", 1, 0))
    graph.add_zone(Zone("D", 2, 0))

    graph.add_connection("A", "B")
    graph.add_connection("B", "D")
    graph.add_connection("A", "C")
    graph.add_connection("C", "D")

    path = dijkstra(graph, "A", "D")
    print(path)


if __name__ == "__main__":
    main()
