#!/usr/bin/env python3
"""Compare optimized and unoptimized behavior, then inspect MIR stages if available.

Usage:
  python3 scripts/opt_stage_bisect.py --bench=iface_sum
  python3 scripts/opt_stage_bisect.py --bench=match_sum --time --iters=5
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

BENCH_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("XU_ROOT", BENCH_ROOT.parent / "xu")).expanduser().resolve()
sys.path.insert(0, str(ROOT / "scripts"))
from product_compiler import resolve_product_compiler as resolve_hosted_compiler, PRODUCT_RUNNER as HOSTED_RUNNER, product_compile_argv
LANE = "product"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench_crosslang import BY_NAME, xu_src  # noqa: E402
from bench_rusage import run_one  # noqa: E402

PASSES = [
    "lower",
    "inline_const",
    "inline_scalar",
    "inline_rmw",
    "simplify_pre",
    "inline_cfg",
    "lism",
    "cse",
    "copy_prop",
    "late_copy",
    "licm",
    "late_simplify",
    "late_copy2",
    "unroll",
    "unroll_simplify",
]


def compile_run(
    src: Path,
    flags: list[str],
    out: Path,
    expect: str,
    timeout_s: float,
) -> tuple[bool, str, float]:
    env = os.environ.copy()
    src_root = str(ROOT / "src")
    cur = env.get("XUPATH", "")
    if src_root not in cur.split(":"):
        env["XUPATH"] = src_root if not cur else f"{src_root}:{cur}"
    compiler = resolve_hosted_compiler()
    cmd = product_compile_argv(compiler, "build", *flags, str(src), "-o", str(out), runner=HOSTED_RUNNER)
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if p.returncode != 0:
        err = (p.stderr or p.stdout)[-300:].replace("\n", " ")
        return False, f"compile: {err}", 0.0
    os.chmod(out, 0o755)
    s = run_one([str(out)], timeout_s=timeout_s)
    text = s.stdout.decode("utf-8", "replace")
    if s.returncode != 0:
        return False, f"run rc={s.returncode} wall={s.wall_s:.1f}s", s.wall_s
    if text != expect:
        return False, f"MISMATCH {text!r}", s.wall_s
    return True, "OK", s.wall_s


def median(xs: list[float]) -> float:
    ys = sorted(xs)
    n = len(ys)
    if n == 0:
        return 0.0
    if n % 2 == 1:
        return ys[n // 2]
    return 0.5 * (ys[n // 2 - 1] + ys[n // 2])


def compile_run_med(
    src: Path,
    flags: list[str],
    out: Path,
    expect: str,
    timeout_s: float,
    iters: int,
) -> tuple[bool, str, float]:
    ok, msg, _wall = compile_run(src, flags, out, expect, timeout_s)
    if not ok:
        return ok, msg, 0.0
    walls: list[float] = []
    for _ in range(max(1, iters)):
        s = run_one([str(out)], timeout_s=timeout_s)
        if s.returncode != 0:
            return False, f"run rc={s.returncode}", s.wall_s
        text = s.stdout.decode("utf-8", "replace")
        if text != expect:
            return False, f"MISMATCH {text!r}", s.wall_s
        walls.append(s.wall_s)
    return True, "OK", median(walls)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bench", default="iface_sum")
    ap.add_argument("--timeout", type=float, default=8.0)
    ap.add_argument("--time", action="store_true", help="report median runtime across repeated samples")
    ap.add_argument("--ra", type=int, choices=(1,), help="select the default register allocator")
    ap.add_argument("--iters", type=int, default=3)
    args = ap.parse_args()
    compiler = resolve_hosted_compiler()
    bench = BY_NAME.get(args.bench)
    if bench is None:
        ap.error(f"unknown bench {args.bench}")

    src = xu_src(args.bench)
    flags = [] if args.ra is None else [f"--ra={args.ra}"]
    suffix = ".exe" if sys.platform == "win32" else ".xin"
    with tempfile.TemporaryDirectory(prefix="xu-opt-bisect-") as directory:
        work = Path(directory)
        results = {}
        for mode, options in (("default", flags), ("no-opt", [*flags, "--no-opt"])):
            out = work / f"{mode}{suffix}"
            if args.time:
                result = compile_run_med(src, options, out, bench.expect, args.timeout, args.iters)
            else:
                result = compile_run(src, options, out, bench.expect, args.timeout)
            ok, message, wall = result
            results[mode] = ok
            print(f"  {mode:<10} {message:40} {wall * 1000:8.1f}ms")

        if all(results.values()):
            return 0
        if not results["default"] and results["no-opt"]:
            help_result = subprocess.run([str(compiler), "build", "--help"],
                                         capture_output=True, text=True, timeout=args.timeout)
            if "--opt-stop" in help_result.stdout:
                dump = work / "stages"
                dump.mkdir()
                for stage in PASSES:
                    ok, message, wall = compile_run(
                        src, [*flags, "--opt-stop", stage, "--dump-opt-stages", str(dump)],
                        work / f"{stage}{suffix}", bench.expect, args.timeout)
                    print(f"  stop={stage:<18} {message:40} {wall * 1000:8.1f}ms")
                    if not ok:
                        break
            else:
                print("The optimized build failed and the unoptimized build matched. This compiler has no stage-stop option.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
