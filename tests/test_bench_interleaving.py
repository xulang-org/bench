"""Exercise host drift, transient wrong output, and failures in tier sampling."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bench_opt_levels as levels


class InterleavedSamplingTests(unittest.TestCase):
    def sample(self, wall=0.01, stdout=b"golden\n", rc=0):
        return SimpleNamespace(wall_s=wall, cpu_s=wall, max_rss_mib=2.0,
                               stdout=stdout, stderr=b"failure", returncode=rc,
                               rss_curve=())

    def measure(self, bins, **kwargs):
        return levels.timed_interleaved(
            bins, kwargs.pop("iters", 8), discard_first=True,
            sample_interval_s=kwargs.pop("sample_interval_s", None),
            cwd=Path.cwd(), expect=b"golden\n", **kwargs,
        )

    def test_equal_kernels_stay_equal_under_linear_host_drift(self):
        bins = {("xu", opt): Path(str(opt)) for opt in range(4)}
        order = []

        def drifting(cmd, **kwargs):
            order.append(cmd[0])
            return self.sample(wall=0.01 + len(order) * 0.001)

        with patch.object(levels, "run_one", side_effect=drifting):
            rows, errors = self.measure(bins)
        self.assertFalse(errors)
        self.assertEqual(len(order), 36)  # Four warmups plus eight rounds.
        self.assertEqual(order[0], "1")  # O1 establishes the timeout anchor.
        for path in bins.values():
            self.assertEqual(order.count(str(path)), 9)
        medians = [row.med_s for row in rows.values()]
        self.assertAlmostEqual(max(medians), min(medians))

    def test_wrong_warmup_or_iteration_cannot_be_overwritten(self):
        for bad_run in (1, 4, 6):  # Warmup, measured run, RSS curve.
            count = 0

            def transient(cmd, **kwargs):
                nonlocal count
                count += 1
                return self.sample(stdout=b"wrong\n" if count == bad_run else b"golden\n")

            with patch.object(levels, "run_one", side_effect=transient):
                rows, errors = self.measure({("xu", 1): Path("1")}, iters=4,
                                            sample_interval_s=0.005)
            self.assertFalse(errors)
            self.assertEqual(rows[("xu", 1)].stdout, "wrong\n")

    def test_one_failed_tier_keeps_other_tiers_and_timeout(self):
        timeouts = []

        def failing(cmd, **kwargs):
            if cmd[0] == "3":
                timeouts.append(kwargs["timeout_s"])
                return self.sample(rc=7)
            return self.sample()

        with patch.object(levels, "run_one", side_effect=failing):
            rows, errors = self.measure({("xu", opt): Path(str(opt)) for opt in (1, 2, 3)})
        self.assertEqual(set(rows), {("xu", 1), ("xu", 2)})
        self.assertIn("run failed", errors[("xu", 3)])
        self.assertEqual(timeouts, [1.0])

    def test_measured_o1_uses_same_watchdog_as_other_tiers(self):
        observed = []

        def watchdog(cmd, **kwargs):
            observed.append((cmd[0], kwargs["timeout_s"]))
            return self.sample()

        with patch.object(levels, "run_one", side_effect=watchdog):
            self.measure({("xu", opt): Path(str(opt)) for opt in (1, 2, 3)}, iters=2)
        self.assertEqual(observed[0], ("1", None))
        self.assertTrue(all(timeout == 1.0 for _, timeout in observed[1:]))

    def test_short_sampling_floor_applies_to_every_tier(self):
        for cpu, expected_runs in ((0.01, 10), (0.1, 6)):
            with patch.object(levels, "run_one", return_value=self.sample(wall=cpu)) as run:
                rows, errors = self.measure({("xu", opt): Path(str(opt)) for opt in (1, 2)},
                                            iters=2, short_iters=4)
            self.assertFalse(errors)
            self.assertEqual(len(rows), 2)
            self.assertEqual(run.call_count, expected_runs)


if __name__ == "__main__":
    unittest.main()
