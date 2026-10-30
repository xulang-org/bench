"""The product wrapper must retain argument and failure boundaries on Windows."""
from pathlib import Path
import math
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import product_compiler


def test_windows_uses_git_bash_without_interpolating_arguments(monkeypatch):
    runner = Path("wrapper with spaces.sh")
    compiler = Path("compiler with spaces.exe")
    arguments = ["build", "source ' $name; file.xu", "-o", "output with spaces.xin"]
    with monkeypatch.context() as context:
        context.setattr(product_compiler.sys, "platform", "win32")
        context.setattr(product_compiler, "git_bash", lambda: Path("git bash.exe"))
        command = product_compiler.product_compile_argv(compiler, *arguments, runner=runner)
    assert command == ["git bash.exe", runner.as_posix(), str(compiler), *arguments]


def test_unix_keeps_direct_wrapper_execution(monkeypatch):
    with monkeypatch.context() as context:
        context.setattr(product_compiler.sys, "platform", "linux")
        command = product_compiler.product_compile_argv(Path("xu"), "build", runner=Path("wrapper.sh"))
    assert command == ["wrapper.sh", "xu", "build"]


def test_real_wrapper_launch_preserves_unicode_arguments_and_failure(tmp_path):
    if sys.platform != "win32" and not shutil.which("sh"):
        pytest.skip("POSIX shell unavailable")
    directory = tmp_path / "中文 path ' $literal"
    directory.mkdir()
    runner = directory / "wrapper.sh"
    runner.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\nexit 7\n', encoding="utf-8", newline="\n")
    runner.chmod(0o755)
    compiler = directory / "xu.exe"
    arguments = ["build", "中文 ' $literal; source.xu", "", "-o", "out with spaces.xin"]
    command = product_compiler.product_compile_argv(compiler, *arguments, runner=runner)
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=15)
    assert result.returncode == 7, result.stderr
    assert result.stdout.splitlines() == [str(compiler), *arguments]


@pytest.mark.parametrize("wrapped", [True, False])
def test_windows_compile_metrics_do_not_report_bash_as_the_compiler(tmp_path, monkeypatch, wrapped):
    import bench_opt_levels as levels
    from types import SimpleNamespace
    output = tmp_path / "program.xin"
    def sample(command, **kwargs):
        output.write_bytes(b"compiled")
        return SimpleNamespace(returncode=0, stderr=b"", stdout=b"", wall_s=0.5,
                               max_rss_mib=12.0, cpu_s=0.125)
    command = ["bash.exe", levels.PRODUCT_COMPILER_RUNNER.as_posix()] if wrapped else ["clang.exe", "source.c"]
    with monkeypatch.context() as context:
        context.setattr(levels.sys, "platform", "win32")
        context.setattr(levels, "run_one", sample)
        error, stats = levels.timed_compile(command, output, iters=2, discard_first=True)
    assert error is None
    assert stats.med_s == 0.5
    if wrapped:
        assert math.isnan(stats.med_rss_mib) and math.isnan(stats.med_cpu_s)
    else:
        assert stats.med_rss_mib == 12.0 and stats.med_cpu_s == 0.125
