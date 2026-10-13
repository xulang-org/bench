#!/usr/bin/env python3
"""Focused regression tests for bench_game's untimed full-N output gate."""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import bench_game


class FullOutputGateTests(unittest.TestCase):
    def test_stdout_fingerprint_streams_binary_output(self) -> None:
        payload = bytes(range(256)) * 8193
        with tempfile.TemporaryDirectory() as td:
            program = Path(td) / "emit.py"
            program.write_text(
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "sys.stdout.buffer.write(bytes(range(256)) * int(sys.argv[1]))\n"
            )
            os.chmod(program, 0o755)

            got = bench_game.stdout_fingerprint(program, 8193)

        self.assertEqual(got.length, len(payload))
        self.assertEqual(got.sha256, hashlib.sha256(payload).hexdigest())

    def test_stdout_fingerprint_preserves_run_failure_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            program = Path(td) / "fail.py"
            program.write_text(
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "sys.stderr.write('diagnostic-tail')\n"
                "raise SystemExit(7)\n"
            )
            os.chmod(program, 0o755)

            with self.assertRaisesRegex(RuntimeError, "diagnostic-tail"):
                bench_game.stdout_fingerprint(program, 1)

    def test_full_output_gate_uses_c_reference_and_runs_each_binary_once(self) -> None:
        bench = bench_game.Bench("demo", "demo", 1, 10, "unused")
        bins = {
            ("xu", "demo"): Path("/fake/xu"),
            ("c", "demo"): Path("/fake/c"),
            ("go", "demo"): Path("/fake/go"),
        }
        same = bench_game.StdoutFingerprint(123, "a" * 64)
        logs: list[str] = []

        with mock.patch.object(
            bench_game, "stdout_fingerprint", return_value=same
        ) as fingerprint:
            ok = bench_game.verify_full_stdout(bench, bins, 10, logs.append)

        self.assertTrue(ok)
        self.assertEqual(
            fingerprint.call_args_list,
            [
                mock.call(Path("/fake/c"), 10),
                mock.call(Path("/fake/xu"), 10),
                mock.call(Path("/fake/go"), 10),
            ],
        )
        self.assertTrue(any("REF  c" in line for line in logs))

    def test_full_output_gate_rejects_length_mismatch(self) -> None:
        bench = bench_game.Bench("demo", "demo", 1, 10, "unused")
        bins = {
            ("xu", "demo"): Path("/fake/xu"),
            ("c", "demo"): Path("/fake/c"),
        }
        fingerprints = {
            Path("/fake/c"): bench_game.StdoutFingerprint(10, "a" * 64),
            Path("/fake/xu"): bench_game.StdoutFingerprint(11, "a" * 64),
        }
        logs: list[str] = []

        with mock.patch.object(
            bench_game,
            "stdout_fingerprint",
            side_effect=lambda path, _n: fingerprints[path],
        ):
            ok = bench_game.verify_full_stdout(bench, bins, 10, logs.append)

        self.assertFalse(ok)
        self.assertTrue(any("FAIL xu" in line for line in logs))

    def test_full_output_gate_rejects_digest_mismatch(self) -> None:
        bench = bench_game.Bench("demo", "demo", 1, 10, "unused")
        bins = {
            ("xu", "demo"): Path("/fake/xu"),
            ("c", "demo"): Path("/fake/c"),
        }
        fingerprints = {
            Path("/fake/c"): bench_game.StdoutFingerprint(10, "a" * 64),
            Path("/fake/xu"): bench_game.StdoutFingerprint(10, "b" * 64),
        }

        with mock.patch.object(
            bench_game,
            "stdout_fingerprint",
            side_effect=lambda path, _n: fingerprints[path],
        ):
            ok = bench_game.verify_full_stdout(
                bench, bins, 10, lambda _line: None
            )

        self.assertFalse(ok)

    def test_full_output_gate_discloses_missing_peer(self) -> None:
        bench = bench_game.Bench("demo", "demo", 1, 10, "unused")
        bins = {("xu", "demo"): Path("/fake/xu")}
        logs: list[str] = []

        with mock.patch.object(
            bench_game,
            "stdout_fingerprint",
            return_value=bench_game.StdoutFingerprint(10, "a" * 64),
        ):
            ok = bench_game.verify_full_stdout(bench, bins, 10, logs.append)

        self.assertTrue(ok)
        self.assertTrue(
            any("no cross-implementation comparison" in line for line in logs)
        )


if __name__ == "__main__":
    unittest.main()
