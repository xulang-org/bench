#!/usr/bin/env python3
"""A/B runtime comparison of two Xu compilers on the bench suite.

Usage:
  python3 scripts/bench_ab.py --old ../xu/bin/xu --new /tmp/xu-candidate
  python3 scripts/bench_ab.py --old A --new B --opts 1,2 --benches loop_sum,matmul

Both compilers build every bench with the same hermetic environment
(XU_STDLIB_ROOT=<xu>/src, empty XUPATH). Candidate compilers usually lack
product provenance, so the product runner is not used for either side.

Byte-identical binaries are reported as `same` without timing unless
--time-identical is given (an A/A run that measures the noise floor). Otherwise the
new binary must reproduce the old stdout, and the pair is measured with
bench_opt_levels.timed_interleaved (rotated, mirrored rounds) so host drift
does not bias either side. A bench regresses when the new median CPU time is
slower by both --frac and --abs-ms; every flagged bench is re-measured with
twice the rounds and only confirmed regressions fail the run (exit 1).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_opt_levels as levels  # noqa: E402

BENCH_ROOT = Path(__file__).resolve().parents[1]
BENCH_DIR = BENCH_ROOT / "tests" / "bench"
XU_ROOT = Path(os.environ.get("XU_ROOT", BENCH_ROOT.parent / "xu")).expanduser().resolve()
OLD = (levels.IMPL_XU, 1)
NEW = (levels.IMPL_XU, 2)


def build(xu: Path, src: Path, opt: int, out: Path) -> str | None:
    env = {**os.environ, "XU_STDLIB_ROOT": str(XU_ROOT / "src"), "XUPATH": ""}
    p = subprocess.run([str(xu), "build", f"-O{opt}", str(src), "-o", str(out)],
                       cwd=BENCH_ROOT, env=env, capture_output=True, text=True)
    if p.returncode != 0 or not out.exists():
        return (p.stderr or p.stdout or "no binary")[-300:].replace("\n", " ")
    return None


def golden(binary: Path) -> tuple[bytes | None, str]:
    p = subprocess.run([str(binary)], cwd=BENCH_ROOT, capture_output=True, timeout=120)
    if p.returncode != 0:
        return None, f"exit {p.returncode}"
    return p.stdout, ""


def measure(old: Path, new: Path, expect: bytes, iters: int) -> tuple[float, float, str]:
    stats, errors = levels.timed_interleaved(
        {OLD: old, NEW: new}, iters, discard_first=True, sample_interval_s=None,
        cwd=BENCH_ROOT, expect=expect, short_iters=iters * 3,
    )
    if errors:
        return 0.0, 0.0, "; ".join(f"{'old' if k == OLD else 'new'}: {v}" for k, v in errors.items())
    want = expect.decode("utf-8", "replace")
    for key, side in ((OLD, "old"), (NEW, "new")):
        if stats[key].stdout != want:
            return 0.0, 0.0, f"{side}: stdout differs from old binary"
    return stats[OLD].med_cpu_s, stats[NEW].med_cpu_s, ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old", required=True, type=Path)
    ap.add_argument("--new", required=True, type=Path)
    ap.add_argument("--opts", default="1", help="comma-separated -O levels (default 1)")
    ap.add_argument("--benches", default="", help="comma-separated names (default: all)")
    ap.add_argument("--iters", type=int, default=9)
    ap.add_argument("--frac", type=float, default=0.05)
    ap.add_argument("--abs-ms", type=float, default=0.5)
    ap.add_argument("--time-identical", action="store_true",
                    help="time byte-identical pairs too (A/A noise-floor check)")
    args = ap.parse_args()

    names = [n for n in args.benches.split(",") if n] or sorted(p.stem for p in BENCH_DIR.glob("*.xu"))
    opts = [int(o) for o in args.opts.split(",")]
    regressions: list[str] = []
    failures: list[str] = []
    print(f"{'bench':24} {'O':>2} {'old_ms':>9} {'new_ms':>9} {'ratio':>7}  verdict")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for name in names:
            src = BENCH_DIR / f"{name}.xu"
            for opt in opts:
                o, n = tmp / f"{name}.O{opt}.old", tmp / f"{name}.O{opt}.new"
                eo, en = build(args.old.resolve(), src, opt, o), build(args.new.resolve(), src, opt, n)
                row = f"{name:24} {opt:>2}"
                if eo or en:
                    failures.append(f"{name} O{opt}: build old={'fail' if eo else 'ok'} new={'fail' if en else 'ok'}")
                    print(f"{row} {'-':>9} {'-':>9} {'-':>7}  build: old={eo or 'ok'} new={en or 'ok'}")
                    continue
                if not args.time_identical and o.read_bytes() == n.read_bytes():
                    print(f"{row} {'-':>9} {'-':>9} {'-':>7}  same")
                    continue
                expect, why = golden(o)
                if expect is None:
                    print(f"{row} {'-':>9} {'-':>9} {'-':>7}  old binary failed ({why}); skipped")
                    continue
                old_s, new_s, err = measure(o, n, expect, args.iters)
                if err:
                    failures.append(f"{name} O{opt}: {err}")
                    print(f"{row} {'-':>9} {'-':>9} {'-':>7}  FAIL {err}")
                    continue
                slow = new_s > old_s * (1 + args.frac) and (new_s - old_s) * 1000 > args.abs_ms
                verdict = "ok"
                if slow:
                    old_s, new_s, err = measure(o, n, expect, args.iters * 2)
                    slow = not err and new_s > old_s * (1 + args.frac) and (new_s - old_s) * 1000 > args.abs_ms
                    verdict = "REGRESSION" if slow else "ok (not confirmed on re-run)"
                    if slow:
                        regressions.append(f"{name} O{opt}")
                elif new_s < old_s * (1 - args.frac) and (old_s - new_s) * 1000 > args.abs_ms:
                    verdict = "faster"
                ratio = new_s / old_s if old_s > 0 else 0.0
                print(f"{row} {old_s * 1000:9.2f} {new_s * 1000:9.2f} {ratio:7.3f}  {verdict}")
    for f in failures:
        print("FAIL:", f)
    print(f"bench_ab: {len(regressions)} regression(s), {len(failures)} failure(s)"
          + (": " + ", ".join(regressions) if regressions else ""))
    return 1 if regressions or failures else 0


if __name__ == "__main__":
    sys.exit(main())
