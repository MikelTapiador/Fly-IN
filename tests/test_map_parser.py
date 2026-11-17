"""Map fixtures were counted directly from the supplied text files."""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from algorithms import dijkstra
from map_parser import MapParseError, parse_map
from models import Connection, Graph, Zone, ZoneType


ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / "maps"
# filename: (zones, undirected connections, drones, destination, route cost)
EXPECTED_MAPS = {
    "easy/01_linear_path.txt": (4, 3, 2, "goal", 3),
    "easy/02_simple_fork.txt": (5, 5, 4, "goal", 3),
    "easy/03_basic_capacity.txt": (4, 3, 4, "goal", 3),
    "medium/01_dead_end_trap.txt": (6, 5, 5, "goal", 4),
    "medium/02_circular_loop.txt": (7, 7, 6, "goal", 5),
    "medium/03_priority_puzzle.txt": (7, 7, 5, "goal", 4),
    "hard/01_maze_nightmare.txt": (17, 22, 8, "goal", 6),
    "hard/02_capacity_hell.txt": (15, 21, 12, "goal", 5),
    "hard/03_ultimate_challenge.txt": (31, 37, 15, "goal", 12),
    "challenger/01_the_impossible_dream.txt": (54, 70, 25, "impossible_goal", 19),
}
# All unlisted zones have the default normal type and occupancy of one.
RESTRICTED = {
    "medium/02_circular_loop.txt": {"exit_point"},
    "medium/03_priority_puzzle.txt": {"slow_path1"},
    "hard/01_maze_nightmare.txt": {"trap_loop1", "trap_loop2"},
    "hard/02_capacity_hell.txt": {
        "restricted_tunnel1", "restricted_tunnel2", "restricted_tunnel3",
    },
    "hard/03_ultimate_challenge.txt": {
        "overflow1", "overflow2", "conv_restricted1", "conv_restricted2",
    },
    "challenger/01_the_impossible_dream.txt": {
        "maze_loop1", "maze_loop2", "maze_loop3",
        "maze_loop4", "maze_loop5", "maze_loop6",
        "overflow_hell1", "overflow_hell2", "overflow_hell3",
        "overflow_hell4", "overflow_hell5", "overflow_hell6",
        "conv_restricted1", "conv_restricted2", "conv_restricted3",
        "conv_restricted4", "conv_restricted5", "conv_restricted6",
        "conv_restricted7", "conv_restricted8", "conv_restricted9",
    },
}
PRIORITY = {
    "medium/03_priority_puzzle.txt": {"fast_junction", "fast_path"},
    "hard/01_maze_nightmare.txt": {
        "final_stretch1", "final_stretch2", "final_stretch3",
    },
    "hard/02_capacity_hell.txt": {"priority_bypass1", "priority_bypass2"},
    "hard/03_ultimate_challenge.txt": {
        "priority_hub", "priority_trap1", "priority_trap2", "priority_correct",
        "conv_priority1", "conv_priority2",
    },
    "challenger/01_the_impossible_dream.txt": {
        "false_hope1", "false_hope2", "false_hope3",
        "priority_trap1", "priority_trap2", "priority_trap3", "priority_trap4",
    },
}
OCCUPANCY = {
    "easy/02_simple_fork.txt": {"junction": 2},
    "easy/03_basic_capacity.txt": {"bottleneck": 2, "wide_area": 3},
    "medium/01_dead_end_trap.txt": {"junction": 2},
    "medium/02_circular_loop.txt": {
        "loop_a": 2, "loop_b": 2, "loop_c": 2, "loop_d": 2,
    },
    "medium/03_priority_puzzle.txt": {"fast_junction": 2, "merge_point": 3},
    "hard/01_maze_nightmare.txt": {
        "maze_a1": 2, "maze_b2": 2, "maze_c2": 2,
        "dead_end1": 2, "bottleneck": 2,
    },
    "hard/02_capacity_hell.txt": {
        "waiting_area1": 4, "waiting_area2": 4, "waiting_area3": 4,
        "restricted_tunnel1": 2, "restricted_tunnel2": 2,
        "restricted_tunnel3": 2, "priority_bypass1": 3,
        "priority_bypass2": 3, "convergence": 6, "final_bottleneck": 3,
    },
    "hard/03_ultimate_challenge.txt": {
        "maze_trap2": 3, "maze_loop1": 3, "maze_loop2": 3,
        "maze_loop3": 3, "maze_loop4": 3, "maze_correct": 3,
        "bottleneck1": 2, "overflow1": 3, "overflow2": 3,
        "priority_hub": 4, "priority_correct": 3,
        "conv_restricted1": 2, "conv_restricted2": 2,
        "conv_normal1": 3, "conv_normal2": 3,
        "conv_priority1": 2, "conv_priority2": 2,
        "final_merge": 8, "final_gate1": 3, "final_gate2": 2,
    },
    "challenger/01_the_impossible_dream.txt": {
        "overflow_hell1": 2, "overflow_hell2": 2, "overflow_hell3": 2,
        "overflow_hell4": 2, "overflow_hell5": 2, "overflow_hell6": 2,
        "false_hope1": 3, "false_hope2": 2,
        "final_merge": 5, "final_torture1": 2,
    },
}
# Unlisted links have capacity one; explicit values of one retain that default.
LINK_CAPACITIES = {
    "easy/02_simple_fork.txt": {("start", "junction"): 2},
    "easy/03_basic_capacity.txt": {
        ("start", "bottleneck"): 4, ("bottleneck", "wide_area"): 4,
        ("wide_area", "goal"): 4,
    },
    "medium/01_dead_end_trap.txt": {("start", "junction"): 2},
    "medium/02_circular_loop.txt": {
        ("start", "loop_a"): 2, ("loop_a", "loop_b"): 2,
        ("loop_b", "loop_c"): 2, ("loop_c", "loop_d"): 2,
        ("loop_d", "loop_a"): 2,
    },
    "medium/03_priority_puzzle.txt": {("merge_point", "goal"): 2},
    "hard/01_maze_nightmare.txt": {
        ("start", "maze_a1"): 2, ("start", "dead_end1"): 2,
    },
    "hard/02_capacity_hell.txt": {
        ("priority_bypass2", "convergence"): 2,
        ("convergence", "final_bottleneck"): 3,
    },
    "hard/03_ultimate_challenge.txt": {
        ("start", "dist_gate2"): 2, ("dist_gate2", "maze_trap1"): 2,
        ("maze_trap1", "maze_trap2"): 2, ("maze_correct", "bottleneck1"): 2,
        ("overflow1", "overflow2"): 2, ("conv_priority1", "conv_priority2"): 2,
        ("conv_priority2", "final_merge"): 2, ("final_merge", "final_gate1"): 3,
        ("final_gate1", "final_gate2"): 2, ("final_gate2", "final_gate3"): 2,
        ("final_gate3", "goal"): 2,
    },
}
VALID_MAP = (
    "nb_drones: 2\n"
    "start_hub: START 0 0\n"
    "hub: A 1 0\n"
    "end_hub: END 2 0\n"
    "connection: START-A\n"
    "connection: A-END\n"
)


class SuppliedMapTests(unittest.TestCase):
    def test_all_ten_maps_are_covered_without_windows_metadata(self) -> None:
        actual = {path.relative_to(MAPS).as_posix() for path in MAPS.rglob("*.txt")}
        self.assertEqual(actual, set(EXPECTED_MAPS))
        self.assertEqual(len(actual), 10)

    def test_map_counts_endpoints_and_existing_graph_representation(self) -> None:
        for name, (zones, links, drones, end, _) in EXPECTED_MAPS.items():
            with self.subTest(map=name):
                graph, count, start, finish = parse_map(MAPS / name)
                self.assertIsInstance(graph, Graph)
                self.assertEqual((len(graph.zones), count, start, finish),
                                 (zones, drones, "start", end))
                connections = {
                    link for adjacent in graph.connections.values()
                    for link in adjacent
                }
                self.assertEqual(len(connections), links)
                for link in connections:
                    self.assertIsInstance(link, Connection)
                    self.assertIs(link.origin, graph.zones[link.origin.name])
                    self.assertIs(link.destination, graph.zones[link.destination.name])
                    self.assertIn(link, graph.connections[link.origin.name])
                    self.assertIn(link, graph.connections[link.destination.name])

    def test_every_zone_type_and_occupancy(self) -> None:
        for name in EXPECTED_MAPS:
            with self.subTest(map=name):
                graph, _, _, _ = parse_map(MAPS / name)
                self.assertTrue(RESTRICTED.get(name, set()) <= graph.zones.keys())
                self.assertTrue(PRIORITY.get(name, set()) <= graph.zones.keys())
                self.assertTrue(OCCUPANCY.get(name, {}).keys() <= graph.zones.keys())
                for zone_name, zone in graph.zones.items():
                    expected = ZoneType.NORMAL
                    if zone_name in RESTRICTED.get(name, set()):
                        expected = ZoneType.RESTRICTED
                    elif zone_name in PRIORITY.get(name, set()):
                        expected = ZoneType.PRIORITY
                    self.assertIs(zone.zone_type, expected, zone_name)
                    self.assertEqual(
                        zone.max_drones, OCCUPANCY.get(name, {}).get(zone_name, 1),
                        zone_name,
                    )

    def test_all_connection_capacities(self) -> None:
        for name in EXPECTED_MAPS:
            with self.subTest(map=name):
                graph, _, _, _ = parse_map(MAPS / name)
                expected = {
                    frozenset(endpoints): capacity
                    for endpoints, capacity in LINK_CAPACITIES.get(name, {}).items()
                }
                actual = {}
                for adjacent in graph.connections.values():
                    for link in adjacent:
                        pair = frozenset((link.origin.name, link.destination.name))
                        actual[pair] = link.capacity
                self.assertTrue(expected.keys() <= actual.keys())
                for pair, capacity in actual.items():
                    self.assertEqual(capacity, expected.get(pair, 1), pair)

    def test_colors_and_negative_coordinates_from_each_category(self) -> None:
        examples = [
            ("easy/01_linear_path.txt", "waypoint1", 1, 0, "blue"),
            ("easy/02_simple_fork.txt", "path_b", 2, -1, "blue"),
            ("easy/03_basic_capacity.txt", "bottleneck", 1, 0, "orange"),
            ("medium/01_dead_end_trap.txt", "dead_end", 1, 1, "red"),
            ("medium/02_circular_loop.txt", "exit_point", 3, 0, "blue"),
            ("medium/03_priority_puzzle.txt", "slow_path1", 1, -1, "red"),
            ("hard/01_maze_nightmare.txt", "dead_end3", 2, -1, "red"),
            ("hard/02_capacity_hell.txt", "start", 0, -1, "green"),
            ("hard/03_ultimate_challenge.txt", "goal", 13, 0, "gold"),
            ("challenger/01_the_impossible_dream.txt",
             "impossible_goal", 23, 0, "rainbow"),
        ]
        for name, zone_name, x, y, color in examples:
            with self.subTest(map=name, zone=zone_name):
                graph, _, _, _ = parse_map(MAPS / name)
                zone = graph.zones[zone_name]
                self.assertEqual((zone.x, zone.y, zone.color), (x, y, color))

    def test_dijkstra_compatibility_and_independent_route_costs(self) -> None:
        for name, (_, _, _, _, expected_cost) in EXPECTED_MAPS.items():
            with self.subTest(map=name):
                graph, _, start, end = parse_map(MAPS / name)
                route = dijkstra(graph, start, end)
                self.assertTrue(route)
                self.assertEqual((route[0], route[-1]), (start, end))
                for origin, destination in zip(route, route[1:]):
                    self.assertIn(graph.zones[destination], graph.get_neighbors(origin))
                self.assertEqual(
                    sum(graph.zones[zone].movement_cost() for zone in route[1:]),
                    expected_cost,
                )


class ParserTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)

    def write_map(self, text: str = VALID_MAP, name: str = "map.txt") -> Path:
        path = self.directory / name
        path.write_text(text, encoding="utf-8")
        return path

    def assert_invalid(self, text: str, line: int, reason: str) -> None:
        path = self.write_map(text)
        with self.assertRaises(MapParseError) as caught:
            parse_map(path)
        error = caught.exception
        self.assertEqual(error.filename, path)
        self.assertEqual(error.line_number, line)
        self.assertIn(f"{path}:{line}:", str(error))
        self.assertRegex(error.reason, reason)

    def test_defaults_and_string_path(self) -> None:
        graph, drones, start, end = parse_map(str(self.write_map()))
        self.assertEqual((drones, start, end), (2, "START", "END"))
        self.assertIsInstance(graph.zones["A"], Zone)
        self.assertIs(graph.zones["A"].zone_type, ZoneType.NORMAL)
        self.assertEqual(graph.zones["A"].max_drones, 1)
        self.assertIsNone(graph.zones["A"].color)
        self.assertEqual(graph.connections["A"][0].capacity, 1)
        self.assertEqual([zone.name for zone in graph.get_neighbors("START")], ["A"])

    def test_whitespace_comments_hex_colors_and_attribute_order(self) -> None:
        path = self.write_map(
            " \t# Heading\n\n"
            " nb_drones \t: +2 # drones\n"
            " start_hub: origin\t-2 +0 [ max_drones = 3 color=#00ff00 ] # start\n"
            " hub: A +1 -1 [color=purple zone = priority max_drones=2]\n"
            " end_hub: finish 2 0 []\n"
            " connection : origin - A [ max_link_capacity = 2 ] # edge\n"
            " connection: A-finish\n"
            " # Last comment\n"
        )
        graph, drones, start, end = parse_map(path)
        self.assertEqual((drones, start, end), (2, "origin", "finish"))
        origin = graph.zones[start]
        self.assertEqual((origin.x, origin.y, origin.color, origin.max_drones),
                         (-2, 0, "#00ff00", 3))
        self.assertIs(graph.zones["A"].zone_type, ZoneType.PRIORITY)
        self.assertEqual(graph.zones["A"].max_drones, 2)
        self.assertEqual(graph.connections[start][0].capacity, 2)

    def test_all_documented_zone_types_including_blocked(self) -> None:
        text = VALID_MAP.replace("hub: A 1 0", "hub: A 1 0 [zone=restricted]")
        text += "hub: P 3 0 [zone=priority]\nhub: B 4 0 [zone=blocked]\n"
        graph, _, _, _ = parse_map(self.write_map(text))
        self.assertIs(graph.zones["START"].zone_type, ZoneType.NORMAL)
        self.assertIs(graph.zones["A"].zone_type, ZoneType.RESTRICTED)
        self.assertIs(graph.zones["P"].zone_type, ZoneType.PRIORITY)
        self.assertIs(graph.zones["B"].zone_type, ZoneType.BLOCKED)
        self.assertEqual(graph.zones["A"].movement_cost(), 2)
        self.assertEqual(graph.zones["B"].movement_cost(), float("inf"))

    def test_forward_references_and_arbitrary_definition_order(self) -> None:
        text = (
            "connection: A-END\nconnection: START-A [max_link_capacity=2]\n"
            "end_hub: END 2 0\nhub: A 1 0\nstart_hub: START 0 0\nnb_drones: 2\n"
        )
        graph, drones, start, end = parse_map(self.write_map(text))
        self.assertEqual((drones, start, end), (2, "START", "END"))
        self.assertEqual(graph.connections[start][0].capacity, 2)
        self.assertEqual(dijkstra(graph, start, end), ["START", "A", "END"])

    def test_utf8_bom_and_windows_line_endings(self) -> None:
        path = self.directory / "windows.txt"
        path.write_bytes(b"\xef\xbb\xbf" + VALID_MAP.replace("\n", "\r\n").encode())
        graph, drones, start, end = parse_map(path)
        self.assertEqual((len(graph.zones), drones, start, end), (3, 2, "START", "END"))

    def test_repeated_calls_do_not_share_graph_state(self) -> None:
        path = self.write_map()
        first, _, _, _ = parse_map(path)
        second, _, _, _ = parse_map(path)
        first.add_zone(Zone("extra", 0, 3))
        self.assertNotIn("extra", second.zones)
        self.assertIsNot(first.zones["A"], second.zones["A"])

    def test_disconnected_maps_and_blocked_endpoints_remain_loadable(self) -> None:
        for text in (
            "nb_drones: 1\nstart_hub: origin 0 0\nend_hub: target 1 0\n",
            VALID_MAP.replace("end_hub: END 2 0", "end_hub: END 2 0 [zone=blocked]"),
        ):
            with self.subTest(text=text):
                graph, _, start, end = parse_map(self.write_map(text))
                self.assertEqual(dijkstra(graph, start, end), [])

    def test_empty_and_comment_only_files(self) -> None:
        self.assert_invalid("", 1, "missing required.*nb_drones.*start_hub.*end_hub")
        self.assert_invalid("# only a comment\n\n", 3, "missing required")

    def test_missing_required_definitions(self) -> None:
        for line, directive in [(0, "nb_drones"), (1, "start_hub"), (3, "end_hub")]:
            with self.subTest(directive=directive):
                lines = VALID_MAP.splitlines()
                del lines[line]
                self.assert_invalid("\n".join(lines), 6, f"missing required.*{directive}")

    def test_duplicate_drone_count_and_terminal_roles(self) -> None:
        examples = [
            ("nb_drones: 3\n", "duplicate nb_drones"),
            ("start_hub: other 4 0\n", "multiple start_hub"),
            ("end_hub: other 4 0\n", "multiple end_hub"),
        ]
        for extra, reason in examples:
            with self.subTest(extra=extra):
                self.assert_invalid(VALID_MAP + extra, 7, reason)

    def test_duplicate_zone_names_including_start_end_alias(self) -> None:
        self.assert_invalid(VALID_MAP + "hub: A 9 9\n", 7, "Zone already exists")
        self.assert_invalid(
            VALID_MAP.replace("end_hub: END", "end_hub: START"), 4,
            "Zone already exists",
        )

    def test_duplicate_connections_in_either_direction(self) -> None:
        for connection in ("START-A", "A-START"):
            with self.subTest(connection=connection):
                self.assert_invalid(
                    VALID_MAP + f"connection: {connection}\n", 7,
                    "Connection already exists",
                )

    def test_unknown_zone_references_preserve_connection_line_number(self) -> None:
        self.assert_invalid(
            "connection: START-missing\n" + VALID_MAP, 1,
            "connection START-missing: Zone does not exist",
        )

    def test_self_connections_use_graph_validation(self) -> None:
        self.assert_invalid(
            VALID_MAP + "connection: A-A\n", 7, "cannot connect to itself",
        )

    def test_nonpositive_drone_counts(self) -> None:
        for value in ("0", "-1"):
            with self.subTest(value=value):
                self.assert_invalid(
                    VALID_MAP.replace("nb_drones: 2", f"nb_drones: {value}"),
                    1, "positive integer",
                )

    def test_invalid_numeric_syntax_for_every_integer_field(self) -> None:
        fields = [
            ("nb_drones: 2", "nb_drones: {value}", 1),
            ("hub: A 1 0", "hub: A {value} 0", 3),
            ("hub: A 1 0", "hub: A 1 {value}", 3),
            ("hub: A 1 0", "hub: A 1 0 [max_drones={value}]", 3),
            ("connection: START-A",
             "connection: START-A [max_link_capacity={value}]", 5),
        ]
        for original, replacement, line in fields:
            for value in ("1.5", "true", "1_000", "nan", "0x10", "\u0662"):
                with self.subTest(field=replacement, value=value):
                    self.assert_invalid(
                        VALID_MAP.replace(original, replacement.format(value=value)),
                        line, "must be an integer",
                    )

    def test_oversized_integer_is_reported_as_an_input_error(self) -> None:
        get_limit = getattr(sys, "get_int_max_str_digits", None)
        if get_limit is None or not get_limit():
            self.skipTest("Python has no active integer conversion limit")
        value = "9" * (get_limit() + 1)
        self.assert_invalid(
            VALID_MAP.replace("nb_drones: 2", f"nb_drones: {value}"),
            1, "too large to read as an integer",
        )

    def test_long_malformed_attribute_is_rejected(self) -> None:
        attribute = "a" * 20_000
        self.assert_invalid(
            VALID_MAP.replace("hub: A 1 0", f"hub: A 1 0 [{attribute}]"),
            3, "malformed attribute",
        )

    def test_nonpositive_capacities_use_existing_models(self) -> None:
        for value in ("0", "-2"):
            with self.subTest(value=value):
                self.assert_invalid(
                    VALID_MAP.replace("hub: A 1 0", f"hub: A 1 0 [max_drones={value}]"),
                    3, "max_drones must be a positive integer",
                )
                self.assert_invalid(
                    VALID_MAP.replace(
                        "connection: START-A",
                        f"connection: START-A [max_link_capacity={value}]",
                    ),
                    5, "Capacity must be a positive integer",
                )

    def test_unknown_zone_type(self) -> None:
        for value in ("fast", "NORMAL", "Restricted"):
            with self.subTest(value=value):
                self.assert_invalid(
                    VALID_MAP.replace("hub: A 1 0", f"hub: A 1 0 [zone={value}]"),
                    3, "not a valid ZoneType",
                )

    def test_unknown_duplicate_and_misplaced_attributes(self) -> None:
        examples = [
            ("hub: A 1 0", "hub: A 1 0 [colour=blue]", 3, "unknown attribute"),
            ("hub: A 1 0", "hub: A 1 0 [max_link_capacity=2]", 3, "unknown attribute"),
            ("hub: A 1 0", "hub: A 1 0 [color=red color=blue]", 3, "duplicate attribute"),
            ("connection: START-A", "connection: START-A [zone=normal]", 5,
             "unknown attribute"),
            ("connection: START-A",
             "connection: START-A [max_link_capacity=1 max_link_capacity=2]", 5,
             "duplicate attribute"),
        ]
        for original, replacement, line, reason in examples:
            with self.subTest(replacement=replacement):
                self.assert_invalid(VALID_MAP.replace(original, replacement), line, reason)

    def test_malformed_attribute_blocks_are_never_ignored(self) -> None:
        for attributes in (
            "[color=]", "[color]", "[=red]", "[color==red]", "[color=red junk]",
            "[color=red", "color=red]", "[[color=red]]", "[color=red] garbage",
            "[color=red][zone=normal]", "[color=red,zone=normal]",
        ):
            with self.subTest(attributes=attributes):
                self.assert_invalid(
                    VALID_MAP.replace("hub: A 1 0", f"hub: A 1 0 {attributes}"),
                    3, "malformed",
                )

    def test_malformed_lines_and_missing_fields(self) -> None:
        for line, reason in (
            ("hub A 1 0", "expected 'directive: value'"),
            ("other: A 1 0", "unknown directive"),
            ("Hub: A 1 0", "unknown directive"),
            ("hub:", "zone name and two"),
            ("hub: A 1", "zone name and two"),
            ("hub: A 1 0 extra", "zone name and two"),
            ("hub: bad-name 1 0", "invalid zone name"),
            ("hub: A:bad 1 0", "invalid zone name"),
            ("hub: A=bad 1 0", "invalid zone name"),
            ("hub: A\x00bad 1 0", "invalid zone name"),
        ):
            with self.subTest(line=line):
                self.assert_invalid(VALID_MAP.replace("hub: A 1 0", line), 3, reason)

    def test_malformed_connections(self) -> None:
        for connection in ("START", "START-A-END", "START--A", "-A", "START-"):
            with self.subTest(connection=connection):
                self.assert_invalid(
                    VALID_MAP.replace("connection: START-A", f"connection: {connection}"),
                    5, "expected a connection|invalid zone name",
                )

    def test_missing_file_and_directory_errors_include_filename(self) -> None:
        for path in (self.directory / "missing.txt", self.directory):
            with self.subTest(path=path):
                with self.assertRaises(MapParseError) as caught:
                    parse_map(path)
                self.assertEqual(caught.exception.filename, path)
                self.assertIsNone(caught.exception.line_number)
                self.assertIn("cannot read map", str(caught.exception))

    def test_permission_errors_are_reported_as_input_errors(self) -> None:
        path = self.write_map()
        with patch.object(Path, "read_text", side_effect=PermissionError(13, "Permission denied")):
            with self.assertRaisesRegex(MapParseError, "Permission denied"):
                parse_map(path)

    def test_invalid_encoding_has_the_correct_line(self) -> None:
        for newline in (b"\n", b"\r\n", b"\r"):
            with self.subTest(newline=newline):
                path = self.directory / "invalid.txt"
                path.write_bytes(newline.join([b"# Heading", b"nb_drones: 1", b"\xff"]))
                with self.assertRaises(MapParseError) as caught:
                    parse_map(path)
                self.assertEqual(caught.exception.line_number, 3)
                self.assertIn("invalid UTF-8", str(caught.exception))

    def test_windows_metadata_is_not_treated_as_a_map(self) -> None:
        for suffix in (":Zone.Identifier", "\uf03aZone.Identifier"):
            with self.subTest(suffix=suffix):
                path = self.write_map(VALID_MAP, "map.txt" + suffix)
                with self.assertRaisesRegex(MapParseError, "Windows metadata"):
                    parse_map(path)


if __name__ == "__main__":
    unittest.main()
