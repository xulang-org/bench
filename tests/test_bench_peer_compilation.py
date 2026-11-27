"""Compile real reference programs through the optimization benchmark driver."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bench_crosslang as crosslang
import bench_opt_levels as levels
from bench_crosslang import BENCHES, cross_src


class PeerCompilationTests(unittest.TestCase):
    def compile_and_run(self, tool, ext, bench, argv_fn):
        with tempfile.TemporaryDirectory(prefix="xu-peer-test-") as td:
            out = Path(td) / "program"
            command = argv_fn(tool, cross_src(bench, ext), 1, out)
            built = subprocess.run(command, capture_output=True, text=True, timeout=120)
            self.assertEqual(built.returncode, 0, built.stderr)
            sample = subprocess.run([str(out)], capture_output=True, text=True, timeout=30)
            self.assertEqual(sample.returncode, 0, sample.stderr)
            expected = next(b.expect for b in BENCHES if b.name == bench)
            self.assertEqual(sample.stdout, expected)

    @unittest.skipUnless(shutil.which("go"), "Go reference compiler unavailable")
    def test_go_aes_compiles_with_shared_software_kernel(self):
        self.compile_and_run("go", "go", "aes128_key_setup", levels.go_compile_argv)

    @unittest.skipUnless(shutil.which("swiftc"), "Swift reference compiler unavailable")
    def test_swift_compiles_using_temporary_module_cache(self):
        self.compile_and_run("swiftc", "swift", "startup", levels.swiftc_compile_argv)

    @unittest.skipUnless(shutil.which("swiftc"), "Swift reference compiler unavailable")
    def test_swift_aes_compiles_with_shared_software_kernel(self):
        self.compile_and_run("swiftc", "swift", "aes128_key_setup", levels.swiftc_compile_argv)

    def test_swift_link_flags_match_platform(self):
        with mock.patch.object(crosslang.sys, "platform", "linux"):
            self.assertEqual(crosslang.swift_link_flags(), ["-Xlinker", "-lm"])
            argv = levels.swiftc_compile_argv("swiftc", cross_src("startup", "swift"), 1, Path("/tmp/out"))
            self.assertEqual(argv[-2:], ["-Xlinker", "-lm"])
        for plat in ("darwin", "win32"):
            with mock.patch.object(crosslang.sys, "platform", plat):
                self.assertEqual(crosslang.swift_link_flags(), [])
                argv = levels.swiftc_compile_argv("swiftc", cross_src("startup", "swift"), 1, Path("/tmp/out"))
                self.assertNotIn("-lm", argv)


if __name__ == "__main__":
    unittest.main()
