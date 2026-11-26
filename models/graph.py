from models.zone_and_connection import Zone, Connection


class Graph:
    """A network of named zones connected by undirected links.

    Attributes:
        zones: Zone instances indexed by their unique names.
        connections: Incident connections indexed by zone name. Each
            connection appears in both endpoint lists.
    """

    def __init__(self) -> None:
        """Initialize an empty zone registry and adjacency index."""
        self.zones: dict[str, Zone] = {}
        self.connections: dict[str, list[Connection]] = {}

    def add_zone(self, zone: Zone) -> None:
        """Register a zone and initialize its adjacency list.

        Args:
            zone: Zone whose name identifies it in the graph.

        Raises:
            ValueError: The zone name is already registered.
        """
        if zone.name in self.zones:
            raise ValueError("Zone already exists")

        self.zones[zone.name] = zone
        self.connections[zone.name] = []

    def add_connection(self, connection: Connection) -> None:
        """Register a link in both endpoint adjacency lists.

        Args:
            connection: Link between two registered zone instances.

        Raises:
            ValueError: An endpoint is absent or is a different instance
                from the registered zone, the link joins a zone to itself,
                or the endpoints are already connected in either order.
        """
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
        """List the zones adjacent to a named zone.

        Args:
            name: Name of the zone whose connections to follow.

        Returns:
            Neighboring zones in connection insertion order, or an empty
            list if the zone has no connections.

        Raises:
            KeyError: The zone name is absent from the adjacency index.
        """
        neighbors = []

        for connection in self.connections[name]:
            if connection.origin.name == name:
                neighbors.append(connection.destination)
            else:
                neighbors.append(connection.origin)

        return neighbors
