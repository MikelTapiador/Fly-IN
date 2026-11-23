"""Boundary and error-handling tests for the Fly-in map parser.

Run from the project root:
    python3 -m unittest discover -s tests -p 'test_map_parser.py' -v
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from map_parser import parse_map


BASE = (
    "nb_drones: 2\n"
    "start_hub: start 0 0\n"
    "hub: A 1 0\n"
    "end_hub: goal 2 0\n"
    "connection: start-A\n"
    "connection: A-goal\n"
)


class TestMapParser(unittest.TestCase):
    """Validate valid maps, invalid inputs and diagnostic messages."""

    def parse_text(self, content: str):
        """Create a temporary map and run the real parser against it."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "case.txt"
            path.write_text(content, encoding="utf-8")
            return parse_map(str(path))

    def test_minimal_valid_map(self) -> None:
        graph, drones, start, end = self.parse_text(BASE)
        self.assertEqual(drones, 2)
        self.assertEqual((start, end), ("start", "goal"))
        self.assertEqual(set(graph.zones), {"start", "A", "goal"})
        self.assertEqual(graph.zones["A"].max_drones, 1)
        self.assertEqual(graph.zones["start"].max_drones, 2)
        self.assertEqual(graph.zones["goal"].max_drones, 2)
        self.assertEqual(graph.connections["start"][0].capacity, 1)
        self.assertEqual(len(graph.connections["A"]), 2)
        self.assertIs(
            graph.connections["start"][0],
            graph.connections["A"][0],
        )
        self.assertEqual(
            {zone.name for zone in graph.get_neighbors("A")},
            {"start", "goal"},
        )

    def test_valid_metadata_and_unlimited_special_hubs(self) -> None:
        content = (
            "nb_drones: 4\n"
            "start_hub: start 0 0 [max_drones=invalid color=green]\n"
            "hub: A 1 0 [zone=restricted max_drones=3 color=#00ff00]\n"
            "hub: B 2 0 [color=blue zone=priority max_drones=4]\n"
            "end_hub: goal 3 0 [max_drones=-50]\n"
            "connection: start-A [max_link_capacity=2]\n"
            "connection: A-B [max_link_capacity=4]\n"
            "connection: B-goal\n"
        )
        graph, drones, start, end = self.parse_text(content)
        self.assertEqual((drones, start, end), (4, "start", "goal"))
        self.assertEqual(graph.zones["start"].max_drones, 4)
        self.assertEqual(graph.zones["goal"].max_drones, 4)
        self.assertEqual(graph.zones["A"].max_drones, 3)
        self.assertEqual(graph.zones["A"].zone_type.value, "restricted")
        self.assertEqual(graph.zones["B"].zone_type.value, "priority")
        self.assertEqual(graph.zones["A"].color, "#00ff00")
        self.assertEqual(graph.connections["start"][0].capacity, 2)
        self.assertEqual(graph.connections["B"][0].capacity, 4)

    def test_comments_blank_lines_and_valid_names(self) -> None:
        content = (
            "\n# Comment preceding the first instruction\n"
            "  nb_drones: 1  \n\n"
            "start_hub: start_1 0 0\n"
            "hub: A.b 1 0\n"
            "end_hub: end_2 2 0\n"
            "connection: start_1-A.b\n"
            "connection: A.b-end_2\n"
        )
        graph, drones, start, end = self.parse_text(content)
        self.assertEqual((drones, start, end), (1, "start_1", "end_2"))
        self.assertIn("A.b", graph.zones)

    def test_invalid_lines_report_cause_and_line(self) -> None:
        # (description, source text, message fragment, offending line)
        cases = [
            (
                "nb_drones zero",
                BASE.replace("nb_drones: 2", "nb_drones: 0"),
                "nb_drones must be positive", 1,
            ),
            (
                "nb_drones noninteger",
                BASE.replace("nb_drones: 2", "nb_drones: abc"),
                "nb_drones must be an integer", 1,
            ),
            (
                "nb_drones extra tokens",
                BASE.replace("nb_drones: 2", "nb_drones: 2 3"),
                "Invalid nb_drones format", 1,
            ),
            (
                "duplicate nb_drones",
                BASE.replace("nb_drones: 2\n",
                             "nb_drones: 2\nnb_drones: 3\n"),
                "Duplicate nb_drones", 2,
            ),
            (
                "missing first instruction",
                BASE.replace("nb_drones: 2\n", ""),
                "First instruction must be nb_drones", 1,
            ),
            (
                "missing zone coordinate",
                BASE.replace("hub: A 1 0", "hub: A 1"),
                "Invalid zone format", 3,
            ),
            (
                "noninteger coordinate",
                BASE.replace("hub: A 1 0", "hub: A abc 0"),
                "Invalid coordinates", 3,
            ),
            (
                "zone name with dash",
                BASE.replace("hub: A 1 0", "hub: A-B 1 0"),
                "Invalid zone name", 3,
            ),
            (
                "zone name with space",
                BASE.replace("hub: A 1 0", "hub: A B 1 0"),
                "Invalid coordinates", 3,
            ),
            (
                "duplicate zone name",
                BASE.replace("end_hub: goal 2 0",
                             "hub: A 2 0\nend_hub: goal 2 0"),
                "Zone already exists", 4,
            ),
            (
                "two start hubs",
                BASE.replace("hub: A 1 0", "start_hub: A 1 0"),
                "Multiple start_hub zones", 3,
            ),
            (
                "two end hubs",
                BASE.replace("hub: A 1 0", "end_hub: A 1 0"),
                "Multiple end_hub zones", 4,
            ),
            (
                "unknown instruction",
                BASE.replace("hub: A 1 0", "hubb: A 1 0"),
                "Unknown instruction", 3,
            ),
            (
                "zone missing brackets",
                BASE.replace("hub: A 1 0", "hub: A 1 0 color=blue"),
                "Invalid attributes", 3,
            ),
            (
                "zone broken closing bracket",
                BASE.replace("hub: A 1 0", "hub: A 1 0 [color=blue"),
                "Invalid attributes", 3,
            ),
            (
                "unknown zone attribute",
                BASE.replace("hub: A 1 0", "hub: A 1 0 [colour=red]"),
                "Unknown zone attribute", 3,
            ),
            (
                "repeated zone attribute",
                BASE.replace("hub: A 1 0",
                             "hub: A 1 0 [color=red color=blue]"),
                "Duplicate attribute", 3,
            ),
            (
                "attribute without equals",
                BASE.replace("hub: A 1 0", "hub: A 1 0 [color]"),
                "Invalid attribute format", 3,
            ),
            (
                "attribute without value",
                BASE.replace("hub: A 1 0", "hub: A 1 0 [color=]"),
                "Empty attribute", 3,
            ),
            (
                "attribute without key",
                BASE.replace("hub: A 1 0", "hub: A 1 0 [=blue]"),
                "Empty attribute", 3,
            ),
            (
                "zone capacity zero",
                BASE.replace("hub: A 1 0", "hub: A 1 0 [max_drones=0]"),
                "max_drones must be positive", 3,
            ),
            (
                "zone capacity noninteger",
                BASE.replace("hub: A 1 0", "hub: A 1 0 [max_drones=abc]"),
                "max_drones must be an integer", 3,
            ),
            (
                "unknown zone type",
                BASE.replace("hub: A 1 0", "hub: A 1 0 [zone=fast]"),
                "Invalid zone type", 3,
            ),
            (
                "connection without endpoints",
                BASE.replace("connection: start-A", "connection:"),
                "Invalid connection format", 5,
            ),
            (
                "connection with three endpoints",
                BASE.replace("connection: start-A", "connection: start-A-B"),
                "Invalid connection endpoints", 5,
            ),
            (
                "connection missing destination",
                BASE.replace("connection: start-A", "connection: start-"),
                "Empty connection endpoint", 5,
            ),
            (
                "unknown destination",
                BASE.replace("connection: start-A", "connection: start-X"),
                "Unknown destination zone", 5,
            ),
            (
                "unknown origin",
                BASE.replace("connection: start-A", "connection: X-A"),
                "Unknown origin zone", 5,
            ),
            (
                "self connection",
                BASE.replace("connection: start-A", "connection: start-start"),
                "A zone cannot connect to itself", 5,
            ),
            (
                "duplicate direct connection",
                BASE + "connection: start-A\n",
                "Connection already exists", 7,
            ),
            (
                "duplicate reverse connection",
                BASE + "connection: A-start\n",
                "Connection already exists", 7,
            ),
            (
                "connection too many arguments",
                BASE.replace(
                    "connection: start-A",
                    "connection: start-A [max_link_capacity=2] extra",
                ),
                "Too many connection arguments", 5,
            ),
            (
                "connection missing opening bracket",
                BASE.replace("connection: start-A",
                             "connection: start-A max_link_capacity=2]"),
                "Invalid connection attributes", 5,
            ),
            (
                "connection missing closing bracket",
                BASE.replace("connection: start-A",
                             "connection: start-A [max_link_capacity=2"),
                "Invalid connection attributes", 5,
            ),
            (
                "connection attribute no equals",
                BASE.replace("connection: start-A",
                             "connection: start-A [max_link_capacity]"),
                "Invalid connection attribute format", 5,
            ),
            (
                "connection unknown attribute",
                BASE.replace("connection: start-A",
                             "connection: start-A [capacity=2]"),
                "Unknown connection attribute", 5,
            ),
            (
                "connection capacity noninteger",
                BASE.replace("connection: start-A",
                             "connection: start-A [max_link_capacity=abc]"),
                "max_link_capacity must be a number", 5,
            ),
            (
                "connection capacity zero",
                BASE.replace("connection: start-A",
                             "connection: start-A [max_link_capacity=0]"),
                "max_link_capacity must be positive", 5,
            ),
        ]

        for name, content, message, line_number in cases:
            with self.subTest(case=name):
                with self.assertRaises(ValueError) as context:
                    self.parse_text(content)
                actual = str(context.exception)
                self.assertIn(message, actual)
                self.assertIn(f":{line_number}:", actual)

    def test_missing_required_hubs_and_empty_file(self) -> None:
        cases = [
            ("empty file", "", "Missing nb_drones"),
            (
                "missing start hub",
                BASE.replace("start_hub:", "hub:"),
                "start_hub",
            ),
            (
                "missing end hub",
                BASE.replace("end_hub:", "hub:"),
                "end_hub",
            ),
        ]
        for name, content, message in cases:
            with self.subTest(case=name):
                with self.assertRaises(ValueError) as context:
                    self.parse_text(content)
                actual = str(context.exception)
                self.assertIn(message, actual)
                # EOF diagnostics must also identify the source file.
                self.assertIn("case.txt:EOF:", actual)


if __name__ == "__main__":
    unittest.main()
