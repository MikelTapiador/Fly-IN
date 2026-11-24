from models import Zone, Graph, Connection
from pathlib import Path


def parse_map(filename: str | Path) -> tuple[Graph, int, str, str]:

    graph = Graph()
    nb_drones = None
    start_name = None
    end_name = None

    with open(filename, "r") as file:
        for line_number, line in enumerate(file, start=1):
            try:
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                parts = line.split()
                instruction = parts[0]

                if nb_drones is None and instruction != "nb_drones:":
                    raise ValueError("First instruction must be nb_drones")

                if instruction == "nb_drones:":
                    if nb_drones is not None:
                        raise ValueError("Duplicate nb_drones")

                    if len(parts) != 2:
                        raise ValueError("Invalid nb_drones format")

                    try:
                        nb_drones = int(parts[1])
                    except ValueError:
                        raise ValueError("nb_drones must be an integer")

                    if nb_drones <= 0:
                        raise ValueError("nb_drones must be positive")

                elif instruction in ("start_hub:", "hub:", "end_hub:"):
                    if len(parts) < 4:
                        raise ValueError("Invalid zone format")

                    name = parts[1]

                    if "-" in name:
                        raise ValueError(f"Invalid zone name: {name}")

                    try:
                        x = int(parts[2])
                        y = int(parts[3])
                    except ValueError:
                        raise ValueError(
                            f"Invalid coordinates for zone '{name}'")

                    attributes = " ".join(parts[4:])

                    if attributes:
                        if (
                            not attributes.startswith("[")
                            or not attributes.endswith("]")
                        ):
                            raise ValueError(
                                f"Invalid attributes for zone '{name}'"
                            )

                        attributes = attributes[1:-1]

                    zone_attributes = {}

                    allowed_attributes = {"zone", "color", "max_drones"}

                    for attribute in attributes.split():
                        if attribute.count("=") != 1:
                            raise ValueError("Invalid attribute format")

                        key, value = attribute.split("=")

                        if not key or not value:
                            raise ValueError("Empty attribute key or value")

                        if key in zone_attributes:
                            raise ValueError(f"Duplicate attribute: {key}")

                        zone_attributes[key] = value

                    for key in zone_attributes:
                        if key not in allowed_attributes:
                            raise ValueError(f"Unknown zone attribute: {key}")

                    max_drones = 1

                    if instruction in ("start_hub:", "end_hub:"):
                        assert nb_drones is not None
                        max_drones = nb_drones

                    elif "max_drones" in zone_attributes:
                        try:
                            max_drones = int(zone_attributes["max_drones"])
                        except ValueError:
                            raise ValueError("max_drones must be an integer")

                        if max_drones <= 0:
                            raise ValueError("max_drones must be positive")

                    if "zone" in zone_attributes:
                        zone_type = zone_attributes["zone"]

                        allowed_zones = {
                            "normal",
                            "restricted",
                            "priority",
                            "blocked"
                        }

                        if zone_type not in allowed_zones:
                            raise ValueError(f"Invalid zone type: {zone_type}")

                    zone_type = zone_attributes.get("zone", "normal")
                    color = zone_attributes.get("color")

                    zone = Zone(
                        name=name,
                        x=x,
                        y=y,
                        zone_type=zone_type,
                        max_drones=max_drones,
                        color=color
                        )

                    graph.add_zone(zone)

                    if instruction == "start_hub:":
                        if start_name is not None:
                            raise ValueError("Multiple start_hub zones")
                        start_name = name

                    elif instruction == "end_hub:":
                        if end_name is not None:
                            raise ValueError("Multiple end_hub zones")
                        end_name = name

                elif instruction == "connection:":
                    if len(parts) < 2:
                        raise ValueError("Invalid connection format")

                    endpoints = parts[1].split("-")

                    if len(endpoints) != 2:
                        raise ValueError("Invalid connection endpoints")

                    origin, destination = endpoints

                    if not origin or not destination:
                        raise ValueError("Empty connection endpoint")

                    if origin not in graph.zones:
                        raise ValueError(f"Unknown origin zone: {origin}")

                    if destination not in graph.zones:
                        raise ValueError(
                            f"Unknown destination zone: {destination}")

                    if len(parts) > 3:
                        raise ValueError("Too many connection arguments")

                    capacity = 1

                    if len(parts) > 2:
                        attribute = parts[2]

                        if not attribute.startswith("["):
                            raise ValueError("Invalid connection attributes")

                        if not attribute.endswith("]"):
                            raise ValueError("Invalid connection attributes")

                        attribute = attribute[1:-1]

                        if attribute.count("=") != 1:
                            raise ValueError(
                                "Invalid connection attribute format")

                        key, value = attribute.split("=")

                        if key != "max_link_capacity":
                            raise ValueError(
                                f"Unknown connection attribute: {key}")

                        try:
                            capacity = int(value)
                        except ValueError:
                            raise ValueError(
                                "max_link_capacity must be a number")

                        if capacity < 1:
                            raise ValueError(
                                "max_link_capacity must be positive")

                    connection = Connection(
                        origin=graph.zones[origin],
                        destination=graph.zones[destination],
                        capacity=capacity
                        )
                    graph.add_connection(connection)

                else:
                    raise ValueError(f"Unknown instruction: {instruction}")

            except ValueError as error:
                raise ValueError(
                    f"{filename}:{line_number}: {error}"
                ) from None

        if nb_drones is None:
            raise ValueError(f"{filename}:EOF: Missing nb_drones")

        if start_name is None or end_name is None:
            raise ValueError(
                f"{filename}:EOF: Missing start_hub or end_hub"
            )

    return graph, nb_drones, start_name, end_name


try:
    parse_map("maps/easy/01_linear_path.txt")
except ValueError as error:
    print(f"Map error: {error}")
