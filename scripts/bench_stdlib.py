#!/usr/bin/env python3
"""Xu standard-library efficiency benchmark suite.

This suite targets `tests/bench/stdlib/*.xu` and measures:
  - compile wall time
  - run best/median wall time
  - median CPU seconds
  - median / max RSS

Usage:
  ./scripts/bench_stdlib.py
  ./scripts/bench_stdlib.py --save
  ./scripts/bench_stdlib.py --check
  ./scripts/bench_stdlib.py --bench=file_rw,time_rand
  ./scripts/bench_stdlib.py --xu=/path/to/bin/xu --iters=5
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import time as _time
import platform
import shutil
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench_crosslang import timed_runs  # noqa: E402

BENCH_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("XU_ROOT", BENCH_ROOT.parent / "xu")).expanduser().resolve()
sys.path.insert(0, str(ROOT / "scripts"))
from product_compiler import resolve_product_compiler as resolve_hosted_compiler, PRODUCT_RUNNER as HOSTED_RUNNER, product_compile_argv
HOST_SEED_RESOLVER = ROOT / "scripts" / "xu_host_seed.sh"
PRODUCT_RUNNER = ROOT / "scripts" / "run_product_compiler.sh"
# Canonical boundary names shared by product consumers.
PRODUCT_COMPILER_RUNNER = PRODUCT_RUNNER
LANE = "product"
DEFAULT_SRC_DIR = BENCH_ROOT / "tests" / "bench" / "stdlib"
DEFAULT_BASELINE = BENCH_ROOT / "reports" / "bench_stdlib.latest.txt"


@dataclass(frozen=True)
class BenchResult:
    name: str
    compile_ms: float
    best_ms: float
    med_ms: float
    med_cpu_ms: float
    med_rss_mib: float
    max_rss_mib: float
    sha1: str
    out: str


def is_executable(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def resolve_compiler(explicit: str | None, lane: str = "product") -> Path:
    if lane != "product":
        raise ValueError(f"unsupported compiler lane: {lane}")
    return resolve_hosted_compiler(explicit)


def resolve_product_xu(explicit: str | None) -> Path:
    """Stable product-lane seam for callers and the boundary checker."""

    return resolve_compiler(explicit, "product")


def sha1_12(payload: str) -> str:
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def compile_src(
    compiler: Path, src: Path, out: Path, *, lane: str
) -> tuple[float, str]:
    if lane != "product":
        raise ValueError(f"unsupported compiler lane: {lane}")
    cmd = product_compile_argv(compiler, "build", str(src), "-o", str(out), runner=PRODUCT_RUNNER)

    t0 = _time.perf_counter()
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    wall_ms = ( _time.perf_counter() - t0) * 1000.0
    if p.returncode != 0 or not out.is_file():
        err = (p.stderr or p.stdout or "unknown compile error").strip()
        return wall_ms, f"compile failed: {err[:2000]}"
    if out.stat().st_size == 0:
        return wall_ms, "compile produced empty binary"
    out.chmod(out.stat().st_mode | 0o111)
    return wall_ms, ""


def load_baseline(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    out: dict[str, dict[str, str]] = {}
    for line in path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 8:
            continue
        name = parts[0]
        rec: dict[str, str] = {}
        for p in parts[1:]:
            if "=" not in p:
                continue
            k, v = p.split("=", 1)
            rec[k] = v
        if rec:
            out[name] = rec
    return out


def fmt_two(v: float) -> str:
    return f"{v:.2f}"


def run_benchmark(
    compiler: Path,
    src: Path,
    tmp_dir: Path,
    iters: int,
    discard_first: bool,
    sample_ms: int | None,
    lane: str,
) -> BenchResult:
    out = tmp_dir / src.with_suffix(".bin").name
    compile_ms, err = compile_src(compiler, src, out, lane=lane)
    if err:
        raise SystemExit(f"{src.name}: compile failed: {err}")

    stats = timed_runs(
        str(out),
        n=iters,
        discard_first=discard_first,
        sample_interval_s=(sample_ms / 1000.0) if sample_ms else None,
    )

    return BenchResult(
        name=src.stem,
        compile_ms=compile_ms,
        best_ms=stats.best_s * 1000.0,
        med_ms=stats.med_s * 1000.0,
        med_cpu_ms=stats.med_cpu_s * 1000.0,
        med_rss_mib=stats.med_rss_mib,
        max_rss_mib=stats.max_rss_mib,
        sha1=sha1_12(stats.stdout),
        out=stats.stdout,
    )


def parse_benches(srcs: list[str] | None, src_dir: Path) -> list[Path]:
    all_paths = sorted(src_dir.glob("*.xu"))
    if not all_paths:
        raise SystemExit(f"bench_stdlib: no .xu files in {src_dir}")
    if not srcs:
        return all_paths

    by_name = {p.stem: p for p in all_paths}
    out = []
    for raw in srcs:
        name = raw.strip()
        if not name:
            continue
        if name not in by_name:
            raise SystemExit(f"bench_stdlib: unknown bench {name!r}; known: {', '.join(sorted(by_name))}")
        out.append(by_name[name])
    if not out:
        raise SystemExit("bench_stdlib: --bench list is empty after filtering")
    return out


def check_gate(
    name: str,
    result: BenchResult,
    baseline: dict[str, str],
    reg_pct: float,
) -> bool:
    old_sha = baseline.get("sha1")
    old_med = baseline.get("med_ms")
    if not old_sha or not old_med:
        raise SystemExit(f"bench_stdlib: baseline for {name} missing fields")
    if result.sha1 != old_sha:
        print(f"  {name}: CHECK FAIL output checksum {result.sha1} != {old_sha}")
        return False
    try:
        old_med_f = float(old_med)
    except ValueError:
        print(f"  {name}: CHECK FAIL baseline median parse error ({old_med!r})")
        return False
    limit = old_med_f * (1.0 + reg_pct)
    if result.med_ms > limit:
        print(
            f"  {name}: CHECK FAIL med_ms {fmt_two(result.med_ms)} > "
            f"{fmt_two(old_med_f)} × {1 + reg_pct:.2f}"
        )
        return False
    return True


def write_baseline(path: Path, results: list[BenchResult], meta: dict[str, str]) -> None:
    lines = [
        f"# bench_stdlib baseline",
        f"# Host: {meta['host']}",
        f"# Compiler: {meta['compiler']}",
        f"# Iters: {meta['iters']}, sample_ms: {meta['sample_ms']}",
    ]
    for r in sorted(results, key=lambda x: x.name):
        lines.append(
            f"{r.name} compile_ms={fmt_two(r.compile_ms)} "
            f"best_ms={fmt_two(r.best_ms)} med_ms={fmt_two(r.med_ms)} "
            f"med_cpu_ms={fmt_two(r.med_cpu_ms)} med_rss_mib={fmt_two(r.med_rss_mib)} "
            f"max_rss_mib={fmt_two(r.max_rss_mib)} sha1={r.sha1}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xu", help="compiler path (product lane by default)")
    ap.add_argument(
        "--lane",
        choices=("product",),
        default="product",
        help="hosted product compiler lane",
    )
    ap.add_argument("--benches", help="comma-separated subset names")
    ap.add_argument("--iters", type=int, default=int(os.getenv("XU_BENCH_ITERS", "7")))
    ap.add_argument("--discard-first", action="store_true")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--src-dir", default=str(DEFAULT_SRC_DIR))
    ap.add_argument("--out", default=str(DEFAULT_BASELINE))
    ap.add_argument("--sample-ms", type=int, default=0)
    ap.add_argument(
        "--regress-pct",
        type=float,
        default=float(os.getenv("STDLIB_BENCH_REGRESS_PCT", "0.10")),
        help="max regression ratio for --check median",
    )

    args = ap.parse_args()
    if args.out:
        Path(args.out).expanduser().parent.mkdir(parents=True, exist_ok=True)
    if args.iters <= 0:
        raise SystemExit("bench_stdlib: --iters must be > 0")
    if args.sample_ms < 0:
        raise SystemExit("bench_stdlib: --sample-ms must be >= 0")

    src_dir = Path(args.src_dir).resolve()
    if not src_dir.is_dir():
        raise SystemExit(f"bench_stdlib: bench dir missing: {src_dir}")

    lane = args.lane
    compiler = resolve_product_xu(args.xu)
    benchmarks = parse_benches(
        [x.strip() for x in args.benches.split(",")] if args.benches else None,
        src_dir,
    )
    if args.list:
        for p in benchmarks:
            print(p.stem)
        return 0

    baseline = load_baseline(Path(args.out))
    if args.check and not baseline:
        raise SystemExit(f"bench_stdlib: --check requested but no baseline: {args.out}")

    reg = args.regress_pct / 100.0

    print(
        f"bench_stdlib: lane={lane} compiler={compiler} "
        f"iters={args.iters} sample_ms={args.sample_ms} "
        f"discard_first={1 if args.discard_first else 0}"
    )
    print(
        "%-18s %10s %10s %10s %10s %11s %11s %12s"
        % ("bench", "compile", "best_ms", "med_ms", "cpu_ms", "rss_med", "rss_max", "sha1")
    )

    tmp = Path(tempfile.mkdtemp(prefix="xu-stdlib-bench-"))
    ok = True
    results: list[BenchResult] = []
    try:
        for src in benchmarks:
            r = run_benchmark(
                compiler,
                src,
                tmp,
                args.iters,
                args.discard_first,
                args.sample_ms,
                lane,
            )
            results.append(r)
            print(
                "%-18s %10s %10s %10s %10s %11s %11s %12s"
                % (
                    r.name,
                    fmt_two(r.compile_ms),
                    fmt_two(r.best_ms),
                    fmt_two(r.med_ms),
                    fmt_two(r.med_cpu_ms),
                    fmt_two(r.med_rss_mib),
                    fmt_two(r.max_rss_mib),
                    r.sha1,
                )
            )
            if args.check and r.name in baseline:
                ok = check_gate(r.name, r, baseline[r.name], reg) and ok
            elif args.check and r.name not in baseline:
                print(f"  {r.name}: CHECK FAIL missing baseline row")
                ok = False
    finally:
        try:
            shutil.rmtree(tmp)
        except OSError:
            pass

    if args.save:
        write_baseline(
            Path(args.out),
            results,
            {
                "host": f"{platform.system()} {platform.machine()}",
                "compiler": str(compiler),
                "lane": lane,
                "iters": str(args.iters),
                "sample_ms": str(args.sample_ms),
            },
        )
        print(f"bench_stdlib: baseline written to {args.out}")
    if not ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
