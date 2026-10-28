"""Shared hosted compiler selection for benchmark entry points."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

BENCH_ROOT = Path(__file__).resolve().parents[1]
xu_env = os.environ.get("XU_ROOT")
if xu_env and (Path(xu_env) / "scripts/xu_host_seed.sh").is_file():
    ROOT = Path(xu_env).expanduser().resolve()
else:
    ROOT = (BENCH_ROOT.parent / "xu").resolve()
PRODUCT_RUNNER = ROOT / "scripts/run_product_compiler.sh"


def git_bash() -> Path:
    git = shutil.which("git")
    roots = list(Path(git).resolve().parents) if git else []
    roots.extend(Path(os.environ[key]) / "Git" for key in
                 ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)") if os.environ.get(key))
    for root in roots:
        bash = root / "bin/bash.exe"
        if bash.is_file():
            return bash
    raise SystemExit("Git for Windows Bash is required for the hosted seed resolver")


def resolve_product_compiler(explicit: str | Path | None = None) -> Path:
    env = os.environ.copy()
    if explicit is not None:
        env["XU_SEED"] = Path(explicit).expanduser().resolve().as_posix()
    if not (ROOT / "scripts/xu_host_seed.sh").is_file():
        raise SystemExit(f"hosted seed resolver missing under XU_ROOT={ROOT}")
    command = [str(ROOT / "scripts/xu_host_seed.sh")]
    if sys.platform == "win32":
        # Native Python cannot execute .sh files or consume MSYS /d/... paths.
        # Run the same resolver in Git Bash and return a Windows-native path.
        # A bare bash may resolve to the WSL launcher on Windows runners.
        command = [str(git_bash()), "-c",
                   'PATH="/usr/bin:/bin:$PATH"; seed=$("$1/scripts/xu_host_seed.sh") || exit; cygpath -w "$seed"',
                   "xu-bench-seed", ROOT.as_posix()]
    proc = subprocess.run(command, cwd=ROOT,
                          env=env, capture_output=True, text=True, check=False)
    lines = proc.stdout.splitlines()
    if proc.returncode or len(lines) != 1:
        raise SystemExit(proc.stderr.strip() or "hosted product compiler unavailable")
    compiler = Path(lines[0])
    if not compiler.is_file() or not os.access(compiler, os.X_OK):
        raise SystemExit(f"compiler is not executable: {compiler}")
    return compiler
