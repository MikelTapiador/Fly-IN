"""Read the map format used by the supplied Fly-in maps."""

from pathlib import Path
import re

from models import Graph, Zone


class MapParseError(ValueError):
    """An invalid or unreadable map, with its source location."""

    def __init__(
        self, filename: Path, line_number: int | None, reason: str
    ) -> None:
        self.filename = filename
        self.line_number = line_number
        self.reason = reason
        location = str(filename)
        if line_number is not None:
            location += f":{line_number}"
        super().__init__(f"{location}: {reason}")


def _strip_comment(line: str) -> str:
    """Remove comments outside attributes; preserve colors such as #00ff00."""
    in_attributes = False
    for index, character in enumerate(line):
        if character == "[":
            in_attributes = True
        elif character == "]":
            in_attributes = False
        elif character == "#" and not in_attributes:
            return line[:index].strip()
    return line.strip()


def _parse_integer(value: str, field: str) -> int:
    if re.fullmatch(r"[+-]?[0-9]+", value) is None:
        raise ValueError(f"{field} must be an integer, got {value!r}")
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(
            f"{field} is too large to read as an integer"
        ) from error


def _validate_name(name: str) -> None:
    if re.fullmatch(r"[^\s:#\[\]=\-\x00-\x1f\x7f]+", name) is None:
        raise ValueError(
            f"invalid zone name {name!r}: expected a token without "
            "whitespace or format delimiters"
        )


def _parse_attributes(payload: str, allowed: set[str]) -> tuple[str, dict[str, str]]:
    """Separate a definition from one optional bracketed attribute block."""
    match = re.fullmatch(r"([^\[\]]*)(?:\[([^\[\]]*)\])?", payload)
    if match is None:
        raise ValueError(
            "malformed attributes: expected one [key=value ...] block"
        )

    fields = match.group(1).strip()
    raw_attributes = (match.group(2) or "").strip()
    attributes: dict[str, str] = {}
    attribute_pattern = re.compile(
        r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^\s=\[\]]+)"
    )
    position = 0
    while position < len(raw_attributes):
        attribute = attribute_pattern.match(raw_attributes, position)
        if attribute is None:
            raise ValueError("malformed attribute: expected key=value")
        key, value = attribute.groups()
        if key not in allowed:
            raise ValueError(f"unknown attribute {key!r}")
        if key in attributes:
            raise ValueError(f"duplicate attribute {key!r}")
        attributes[key] = value
        position = attribute.end()

    return fields, attributes


def _parse_zone(payload: str) -> Zone:
    fields, attributes = _parse_attributes(
        payload, {"zone", "color", "max_drones"}
    )
    parts = fields.split()
    if len(parts) != 3:
        raise ValueError("expected a zone name and two integer coordinates")
    name, x, y = parts
    _validate_name(name)
    return Zone(
        name,
        _parse_integer(x, "x coordinate"),
        _parse_integer(y, "y coordinate"),
        zone_type=attributes.get("zone", "normal"),
        max_drones=_parse_integer(attributes.get("max_drones", "1"), "max_drones"),
        color=attributes.get("color"),
    )


def _parse_connection(payload: str) -> tuple[str, str, int]:
    fields, attributes = _parse_attributes(payload, {"max_link_capacity"})
    parts = fields.split("-")
    if len(parts) != 2:
        raise ValueError(
            "expected a connection in the form origin-destination"
        )
    origin, destination = (part.strip() for part in parts)
    _validate_name(origin)
    _validate_name(destination)
    capacity = _parse_integer(
        attributes.get("max_link_capacity", "1"), "max_link_capacity"
    )
    return origin, destination, capacity


def parse_map(map_path: str | Path) -> tuple[Graph, int, str, str]:
    """Return (graph, nb_drones, start, end), or raise MapParseError.

    Definitions may appear in any order. Connections are added after all zones,
    so forward references work. Model validation remains in Zone and Graph.
    Disconnected maps and blocked endpoints are loadable; routing decides
    reachability. Windows metadata files are not accepted as maps.
    """
    filename = Path(map_path)
    if filename.name.casefold().endswith(
        (":zone.identifier", "\uf03azone.identifier")
    ):
        raise MapParseError(
            filename, None, "Windows metadata is not a map file"
        )
    try:
        text = filename.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as error:
        prefix = error.object[:error.start].replace(b"\r\n", b"\n")
        line_number = prefix.replace(b"\r", b"\n").count(b"\n") + 1
        raise MapParseError(
            filename, line_number, "invalid UTF-8 encoding"
        ) from error
    except OSError as error:
        raise MapParseError(
            filename, None, f"cannot read map: {error.strerror or error}"
        ) from error

    graph = Graph()
    nb_drones: int | None = None
    start: str | None = None
    end: str | None = None
    connections: list[tuple[int, str, str, int]] = []
    lines = text.splitlines()
    for line_number, raw_line in enumerate(lines, start=1):
        line = _strip_comment(raw_line)
        if not line:
            continue
        try:
            directive, separator, payload = line.partition(":")
            if not separator:
                raise ValueError("expected 'directive: value'")
            directive = directive.strip()
            payload = payload.strip()
            if directive == "nb_drones":
                if nb_drones is not None:
                    raise ValueError("duplicate nb_drones definition")
                nb_drones = _parse_integer(payload, "nb_drones")
                if nb_drones <= 0:
                    raise ValueError("nb_drones must be a positive integer")
            elif directive in ("hub", "start_hub", "end_hub"):
                if directive == "start_hub" and start is not None:
                    raise ValueError("multiple start_hub definitions")
                if directive == "end_hub" and end is not None:
                    raise ValueError("multiple end_hub definitions")
                zone = _parse_zone(payload)
                graph.add_zone(zone)
                if directive == "start_hub":
                    start = zone.name
                elif directive == "end_hub":
                    end = zone.name
            elif directive == "connection":
                origin, destination, capacity = _parse_connection(payload)
                connections.append((line_number, origin, destination, capacity))
            else:
                raise ValueError(f"unknown directive {directive!r}")
        except ValueError as error:
            raise MapParseError(
                filename, line_number, str(error)
            ) from error

    if nb_drones is None or start is None or end is None:
        required = {
            "nb_drones": nb_drones, "start_hub": start, "end_hub": end,
        }
        missing = ", ".join(
            key for key, value in required.items() if value is None
        )
        raise MapParseError(
            filename, len(lines) + 1, f"missing required definitions: {missing}"
        )

    for line_number, origin, destination, capacity in connections:
        try:
            graph.add_connection(origin, destination, capacity)
        except ValueError as error:
            raise MapParseError(
                filename, line_number,
                f"connection {origin}-{destination}: {error}",
            ) from error
    return graph, nb_drones, start, end
