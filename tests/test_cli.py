"""Exercise the CLI, including real subprocesses and expected failure modes."""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from main import main


ROOT = Path(__file__).resolve().parents[1]
LINEAR = ROOT / "maps/easy/01_linear_path.txt"
# Counts and costs were read from the files, independently of parser results.
CATEGORIES = [
    ("easy/01_linear_path.txt", 4, 3, 2, "goal", 3),
    ("medium/02_circular_loop.txt", 7, 7, 6, "goal", 5),
    ("hard/03_ultimate_challenge.txt", 31, 37, 15, "goal", 12),
    ("challenger/01_the_impossible_dream.txt", 54, 70, 25, "impossible_goal", 19),
]
SMALL_MAP = (
    "nb_drones: 3\n"
    "start_hub: START 0 0\n"
    "hub: R 1 0 [zone=restricted]\n"
    "end_hub: END 2 0\n"
    "connection: START-R\n"
    "connection: R-END\n"
)


class CLITests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)

    def write_map(self, text: str) -> Path:
        path = self.directory / "map.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def run_main(self, *args: str | Path) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main([str(arg) for arg in args])
        return status, stdout.getvalue(), stderr.getvalue()

    def run_process(self, *args: str | Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(ROOT / "main.py"),
             *(str(arg) for arg in args)],
            cwd=self.directory, text=True, capture_output=True, timeout=20,
        )

    def test_real_cli_and_simulation_in_every_map_category(self) -> None:
        for name, zones, links, drones, end, cost in CATEGORIES:
            for options in ((), ("--simulate",)):
                with self.subTest(map=name, options=options):
                    result = self.run_process(ROOT / "maps" / name, *options)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stderr, "")
                    self.assertIn(f"Zones: {zones}\n", result.stdout)
                    self.assertIn(f"Connections: {links} (bidirectional)\n", result.stdout)
                    self.assertIn(f"Drones: {drones}\n", result.stdout)
                    self.assertIn("START: start\n", result.stdout)
                    self.assertIn(f"END: {end}\n", result.stdout)
                    self.assertIn("Dijkstra route (single drone): start -> ", result.stdout)
                    self.assertIn(f"without congestion): {cost} turn(s)", result.stdout)
                    if options:
                        final_turn = [
                            line for line in result.stdout.splitlines()
                            if line.startswith("Turn ")
                        ][-1]
                        self.assertEqual(
                            final_turn.partition(": ")[2].split(),
                            [f"D{drone}={end}" for drone in range(1, drones + 1)],
                        )
                        self.assertIn("does not optimize routes", result.stdout)
                    else:
                        self.assertNotIn("Simulation turns:", result.stdout)

    def test_info_only_does_not_run_dijkstra_or_simulation(self) -> None:
        with patch("main.dijkstra") as routing, patch("main.run_route") as simulation:
            status, output, error = self.run_main(LINEAR, "--info-only")
        self.assertEqual((status, error), (0, ""))
        self.assertIn("Drones: 2", output)
        self.assertNotIn("Dijkstra route", output)
        routing.assert_not_called()
        simulation.assert_not_called()

    def test_details_include_zone_types_coordinates_and_unique_link_capacities(self) -> None:
        path = ROOT / "maps/easy/02_simple_fork.txt"
        status, output, error = self.run_main(path, "--details", "--info-only")
        self.assertEqual((status, error), (0, ""))
        self.assertIn(
            "junction: (1, 0), zone=normal, max_drones=2, color=yellow", output,
        )
        self.assertIn("path_b: (2, -1)", output)
        self.assertEqual(output.count("junction-start: max_link_capacity=2"), 1)
        self.assertEqual(output.count(": max_link_capacity="), 5)

    def test_output_is_deterministic(self) -> None:
        first = self.run_main(LINEAR, "--details", "--simulate")
        second = self.run_main(LINEAR, "--details", "--simulate")
        self.assertEqual(first, second)
        self.assertEqual(first[0], 0)
        self.assertIn("Simulation turns: 4", first[1])

    def test_simulation_uses_transit_states_for_restricted_zones(self) -> None:
        status, output, error = self.run_main(self.write_map(SMALL_MAP), "--simulate")
        self.assertEqual((status, error), (0, ""))
        self.assertIn("Route travel time (without congestion): 3 turn(s)", output)
        self.assertIn("D1=START->R (in transit)", output)
        self.assertIn("Turn 7: D1=END D2=END D3=END", output)
        self.assertIn("Simulation turns: 7", output)

    def test_missing_and_invalid_files_have_nonzero_exit_and_source_location(self) -> None:
        missing = self.directory / "missing.txt"
        invalid = self.write_map("nb_drones: invalid\n")
        for path, reason in ((missing, "cannot read map"), (invalid, ":1: nb_drones")):
            with self.subTest(path=path):
                result = self.run_process(path)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")
                self.assertIn(str(path), result.stderr)
                self.assertIn(reason, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_unreachable_destination_is_reported_without_attempting_simulation(self) -> None:
        path = self.write_map(
            "nb_drones: 1\nstart_hub: START 0 0\nend_hub: END 1 0\n"
        )
        with patch("main.run_route") as simulation:
            status, output, error = self.run_main(path, "--simulate")
        self.assertEqual(status, 1)
        self.assertIn("Zones: 2", output)
        self.assertIn("no route from START to END", error)
        simulation.assert_not_called()
        self.assertEqual(self.run_main(path, "--info-only")[0], 0)

    def test_blocked_destination_is_reported_as_unreachable(self) -> None:
        path = self.write_map(SMALL_MAP.replace(
            "end_hub: END 2 0", "end_hub: END 2 0 [zone=blocked]",
        ))
        status, _, error = self.run_main(path)
        self.assertEqual(status, 1)
        self.assertIn("no route", error)

    def test_known_simulation_stall_is_reported_gracefully(self) -> None:
        with patch("main.run_route", side_effect=RuntimeError("Simulation stalled")):
            status, output, error = self.run_main(LINEAR, "--simulate")
        self.assertEqual(status, 1)
        self.assertIn("route simulation stalled", error)
        self.assertNotIn("Simulation turns:", output)

    def test_unexpected_routing_errors_are_not_swallowed(self) -> None:
        with patch("main.dijkstra", side_effect=KeyError("programming bug")):
            with self.assertRaisesRegex(KeyError, "programming bug"):
                self.run_main(LINEAR)

    def test_unexpected_parser_errors_are_not_swallowed(self) -> None:
        with patch("main.parse_map", side_effect=RuntimeError("programming bug")):
            with self.assertRaisesRegex(RuntimeError, "programming bug"):
                self.run_main(LINEAR)

    def test_unexpected_simulator_errors_are_not_swallowed(self) -> None:
        for error in (RuntimeError("programming bug"), ValueError("invalid schedule")):
            with self.subTest(error=error):
                with patch("main.run_route", side_effect=error):
                    with self.assertRaises(type(error)):
                        self.run_main(LINEAR, "--simulate")

    def test_argparse_help_and_usage_errors(self) -> None:
        for arguments, status in (
            (("--help",), 0),
            ((), 2),
            ((LINEAR, "--unknown"), 2),
            ((LINEAR, "--simulate", "--info-only"), 2),
        ):
            with self.subTest(arguments=arguments):
                result = self.run_process(*arguments)
                self.assertEqual(result.returncode, status)
                self.assertNotIn("Traceback", result.stderr)
                if status == 0:
                    self.assertIn("--simulate", result.stdout)
                else:
                    self.assertIn("usage:", result.stderr)


if __name__ == "__main__":
    unittest.main()
