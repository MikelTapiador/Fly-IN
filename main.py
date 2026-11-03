from models import Zone
from graph import Graph


def main() -> None:
    graph = Graph()

    graph.add_zone(Zone("A", 0, 0))
    graph.add_zone(Zone("B", 5, 3))

    graph.add_connection("A", "B")

    for neighbor in graph.get_neighbors("A"):
        print(neighbor.name)


if __name__ == "__main__":
    main()
