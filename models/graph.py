from models.zones_and_connections import Zone, Connection


class Graph:
    def __init__(self) -> None:
        self.zones: dict[str, Zone] = {}
        self.connections: dict[str, list[Connection]] = {}

    def add_zone(self, zone: Zone) -> None:
        if zone.name in self.zones:
            raise ValueError("Zone already exists")

        self.zones[zone.name] = zone
        self.connections[zone.name] = []

    def add_connection(self, connection: Connection) -> None:
        a = connection.origin.name
        b = connection.destination.name

        if a not in self.zones or b not in self.zones:
            raise ValueError("Zone does not exist")

        if a == b:
            raise ValueError("A zone cannot connect to itself")

        if (
            self.zones[a] is not connection.origin
            or self.zones[b] is not connection.destination
        ):
            raise ValueError("Connection zones do not belong to graph")

        for existing in self.connections[a]:
            if (
                existing.origin.name == b
                or existing.destination.name == b
            ):
                raise ValueError("Connection already exists")

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
