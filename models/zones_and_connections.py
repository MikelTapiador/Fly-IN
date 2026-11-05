from enum import Enum


class ZoneType(str, Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: ZoneType | str = ZoneType.NORMAL,
        max_drones: int = 1,
        color: str | None = None
    ) -> None:
        if type(max_drones) is not int or max_drones <= 0:
            raise ValueError("max_drones must be a positive integer")

        if type(x) is not int or type(y) is not int:
            raise ValueError("Coordinates must be integers")

        self.name = name
        self.x = x
        self.y = y
        self.zone_type = ZoneType(zone_type)
        self.max_drones = max_drones
        self.color = color

    def movement_cost(self) -> int | float:
        if self.zone_type == ZoneType.BLOCKED:
            return float("inf")

        if self.zone_type == ZoneType.RESTRICTED:
            return 2

        return 1


class Connection:
    def __init__(
        self,
        origin: Zone,
        destination: Zone,
        capacity: int = 1
    ) -> None:
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("Capacity must be a positive integer")

        self.origin = origin
        self.destination = destination
        self.capacity = capacity
