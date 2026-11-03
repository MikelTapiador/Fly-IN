from models import Zone, Connection


class Graph:
    def __init__(self) -> None:
        self.zones: dict[str, Zone] = {}
        self.connections: dict[str, list[Connection]] = {}

    def add_zone(self, zone: Zone) -> None:
        if zone.name in self.zones:
            raise ValueError("Zone already exists")

        self.zones[zone.name] = zone
        self.connections[zone.name] = []

    def add_connection(
        self, a: str, b: str, capacity: int = 1
    ) -> None:
        if a not in self.zones or b not in self.zones:
            raise ValueError("Zone does not exist")

        if a == b:
            raise ValueError("A zone cannot connect to itself")

        for connection in self.connections[a]:
            if connection.origin.name == b or connection.destination.name == b:
                raise ValueError("Connection already exists")

        connection = Connection(
            self.zones[a],
            self.zones[b],
            capacity
        )

        self.connections[a].append(connection)
        self.connections[b].append(connection)

    def get_neighbors(self, name: str) -> list[Zone]:
        neighbors = []

        for connection in self.connections[name]:
            if connection.origin.name == name:
                neighbors.append(connection.destination)
            else:
                neighbors.append(connection.origin)

        return neighbors
