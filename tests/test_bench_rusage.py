"""Optional live RSS collection must not invalidate child execution results."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bench_rusage


class LiveRssPermissionTests(unittest.TestCase):
    def denied_sampler(self):
        return patch.object(bench_rusage.subprocess, "check_output",
                            side_effect=PermissionError("sandbox denies ps"))

    def test_denied_ps_is_an_unavailable_sample(self):
        with patch.object(bench_rusage.sys, "platform", "darwin"), \
                patch.object(bench_rusage, "_init_darwin_rss"), \
                patch.object(bench_rusage, "_darwin_proc_pidinfo", lambda pid: None), \
                self.denied_sampler():
            self.assertIsNone(bench_rusage.rss_bytes_live(12345))

    def test_denied_samples_preserve_output_exit_and_peak_rss(self):
        with patch.object(bench_rusage.sys, "platform", "darwin"), \
                patch.object(bench_rusage, "_init_darwin_rss"), \
                patch.object(bench_rusage, "_darwin_proc_pidinfo", lambda pid: None), \
                self.denied_sampler():
            sample = bench_rusage.run_one(
                [sys.executable, "-c",
                 "import time; time.sleep(0.03); print('observed'); raise SystemExit(7)"],
                sample_interval_s=0.001, timeout_s=5,
            )
        self.assertEqual(sample.returncode, 7)
        self.assertEqual(sample.stdout, b"observed\n")
        self.assertGreater(sample.max_rss_bytes, 0)
        self.assertGreaterEqual(sample.cpu_s, 0)
        self.assertTrue(sample.rss_curve)


if __name__ == "__main__":
    unittest.main()
