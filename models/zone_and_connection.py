from enum import Enum


class ZoneType(str, Enum):
    """Movement categories accepted in map metadata.

    Normal and priority zones take one turn to enter. Restricted zones
    take two turns, and blocked zones cannot be entered.
    """
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:
    """A hub with coordinates, movement rules, and occupancy metadata.

    Attributes:
        name: Zone identifier.
        x: Horizontal map coordinate.
        y: Vertical map coordinate.
        zone_type: Movement category as a ZoneType member.
        max_drones: Stored occupancy limit.
        color: Optional display color name.
    """

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: ZoneType | str = ZoneType.NORMAL,
        max_drones: int = 1,
        color: str | None = None
    ) -> None:

        """Store hub metadata and normalize the movement category.

        Args:
            name: Zone identifier.
            x: Horizontal map coordinate.
            y: Vertical map coordinate.
            zone_type: A ZoneType member or its string value.
            max_drones: Occupancy limit to store.
            color: Optional display color name.

        Raises:
            ValueError: The movement category is not a valid ZoneType.
        """
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = ZoneType(zone_type)
        self.max_drones = max_drones
        self.color = color

    def movement_cost(self) -> int | float:
        """Calculate the cost of entering this zone.

        Returns:
            Two turns for a restricted zone, one for a normal or priority
            zone, or positive infinity for a blocked zone.
        """
        if self.zone_type == ZoneType.BLOCKED:
            return float("inf")

        if self.zone_type == ZoneType.RESTRICTED:
            return 2

        return 1


class Connection:
    """An undirected link with a shared per-turn traversal capacity.

    Attributes:
        origin: First endpoint.
        destination: Second endpoint.
        capacity: Stored limit on simultaneous traversals across the link.
    """

    def __init__(
        self,
        origin: Zone,
        destination: Zone,
        capacity: int = 1
    ) -> None:
        """Store two endpoints and the link capacity.

        Args:
            origin: First endpoint of the link.
            destination: Second endpoint of the link.
            capacity: Per-turn traversal limit shared by both directions.
        """

        self.origin = origin
        self.destination = destination
        self.capacity = capacity
