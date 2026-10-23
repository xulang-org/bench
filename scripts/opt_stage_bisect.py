#!/usr/bin/env python3
"""Locate the first MIR pass (or emit/RA) that breaks a bench.

Compiles with the hosted product `--dump-opt-stages` and `--opt-stop`, then runs the
binary. If every MIR prefix matches expected stdout but O2+RA does not,
the first wrong stage is emit/RA (the iface_sum O2 S2 pin case).

Usage:
  python3 scripts/opt_stage_bisect.py
  python3 scripts/opt_stage_bisect.py --bench=iface_sum --opt=2
  python3 scripts/opt_stage_bisect.py --bench=match_sum --opt=2 --time --ra=1
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
from product_compiler import resolve_product_compiler as resolve_hosted_compiler, PRODUCT_RUNNER as HOSTED_RUNNER
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
    cmd = [str(HOSTED_RUNNER), str(compiler), "build", *flags, str(src), "-o", str(out)]
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", default="iface_sum")
    ap.add_argument("--opt", type=int, default=2)
    ap.add_argument("--timeout", type=float, default=8.0)
    ap.add_argument(
        "--time",
        action="store_true",
        help="walk --opt-stop and find the first pass slower than O1 (same --ra)",
    )
    ap.add_argument(
        "--ra",
        type=int,
        default=None,
        help="pin RA with --ra=N so MIR passes are isolated from S-pool",
    )
    ap.add_argument("--iters", type=int, default=3)
    args = ap.parse_args()
    resolve_hosted_compiler()
    bench = BY_NAME.get(args.bench)
    if bench is None:
        raise SystemExit(f"unknown bench {args.bench}")
    src = xu_src(args.bench)
    tmp = Path(tempfile.mkdtemp(prefix="xu_opt_bisect_"))
    dump = tmp / "stages"
    dump.mkdir()
    expect = bench.expect
    ra_flags = [] if args.ra is None else [f"--ra={args.ra}"]
    ra_note = "" if args.ra is None else f" --ra={args.ra}"
    print(f"# bisect {args.bench} -O{args.opt}{ra_note}  expect={expect!r}")
    print(f"# dump {dump}")
    if args.time:
        return time_walk(src, expect, tmp, dump, args, ra_flags, ra_note)

    configs = [
        ("O0", ["-O0"]),
        ("O1", ["-O1"]),
        (f"O{args.opt}", [f"-O{args.opt}"]),
        (f"O{args.opt} --no-regcache", [f"-O{args.opt}", "--no-regcache"]),
    ]
    results: dict[str, tuple[bool, str, float]] = {}
    for name, flags in configs:
        out = tmp / f"{name.replace(' ', '_')}.xin"
        ok, msg, wall = compile_run(src, flags, out, expect, args.timeout)
        results[name] = (ok, msg, wall)
        print(f"  {name:<28} {msg:40} {wall * 1000:8.1f}ms")

    opt_name = f"O{args.opt}"
    nrc_name = f"O{args.opt} --no-regcache"
    if results[opt_name][0]:
        print(f"# {opt_name} is correct; no broken pass to find")
        return 0
    if not results[nrc_name][0]:
        print(f"# {nrc_name} also wrong → MIR (not RA). Walking --opt-stop.")
        first = None
        for pass_name in PASSES:
            flags = [
                f"-O{args.opt}",
                "--no-regcache",
                "--opt-stop",
                pass_name,
                "--dump-opt-stages",
                str(dump),
            ]
            out = tmp / f"stop_{pass_name}.xin"
            ok, msg, wall = compile_run(src, flags, out, expect, args.timeout)
            print(f"  stop={pass_name:<18} {msg:40} {wall * 1000:8.1f}ms")
            if not ok and first is None:
                first = pass_name
        if first:
            print(f"# first wrong MIR stage: {first}")
            return 1
        print("# all MIR prefixes matched; unexpected")
        return 1
    print(
        f"# {nrc_name} is correct but {opt_name}+RA is not → first wrong stage "
        "is emit/RA (call barrier / pin home), not a MIR transform"
    )
    # Still dump full O-n MIR for the record.
    flags = [
        f"-O{args.opt}",
        "--no-regcache",
        "--dump-opt-stages",
        str(dump),
    ]
    compile_run(src, flags, tmp / "dump.xin", expect, args.timeout)
    print(f"# MIR dumps in {dump}")
    return 1


def time_walk(
    src: Path,
    expect: str,
    tmp: Path,
    dump: Path,
    args,
    ra_flags: list[str],
    ra_note: str,
) -> int:
    """First --opt-stop prefix whose P50 exceeds O1 by 5% and 0.5ms."""
    frac, abs_s = 1.05, 0.0005
    print(f"# time-walk iters={args.iters}  gate: >O1×{frac} and +{abs_s * 1000:.1f}ms")

    def run(tag: str, flags: list[str]) -> tuple[bool, str, float]:
        out = tmp / f"{tag}.xin"
        ok, msg, wall = compile_run_med(
            src, flags, out, expect, args.timeout, args.iters
        )
        print(f"  {tag:<28} {msg:20} {wall * 1000:8.1f}ms")
        return ok, msg, wall

    o1_ok, _, o1 = run("O1", ["-O1", *ra_flags])
    if not o1_ok:
        print("# O1 failed; cannot time-walk")
        return 1
    run(f"O{args.opt}", [f"-O{args.opt}", *ra_flags])
    first = None
    prev = o1
    for pass_name in PASSES:
        ok, _msg, wall = run(
            f"stop={pass_name}",
            [
                f"-O{args.opt}",
                *ra_flags,
                "--opt-stop",
                pass_name,
                "--dump-opt-stages",
                str(dump),
            ],
        )
        if not ok:
            if first is None:
                first = pass_name
            continue
        if wall > o1 * frac and (wall - o1) > abs_s:
            if first is None:
                first = pass_name
                print(
                    f"# first slower than O1: {pass_name}  "
                    f"{wall * 1000:.1f}ms vs O1 {o1 * 1000:.1f}ms "
                    f"(+{(wall / o1 - 1) * 100:.1f}%)  prev {prev * 1000:.1f}ms"
                )
        prev = wall
    if first is None:
        print(f"# no --opt-stop prefix slower than O1{ra_note}")
        return 0
    print(f"# first regressing MIR stage: {first}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
