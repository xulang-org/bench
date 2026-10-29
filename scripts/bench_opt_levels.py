#!/usr/bin/env python3
"""Xu vs Clang vs Go vs Rustc vs Swiftc runtime + resource sweep.

Xu / Clang / rustc: explicit -O0..-O3.
Go: O0 = -gcflags=all=-N -l; O1=O2=O3 = go build (one binary).
Swift: O0 = -Onone; O1=O2=O3 = -O (one binary).

Reports best+median wall, median peak RSS, median CPU (user+sys),
binary size, live RSS curves, and compile wall/RSS of already-built
compilers. Stdout locked per compiler.

Usage:
  ./scripts/bench_opt_full.sh                 # one-command full save + timings
  python3 scripts/bench_opt_levels.py --save
  python3 scripts/bench_opt_levels.py --lane product --xu ./bin/xu --check
  python3 scripts/bench_opt_levels.py --skip-runtime --save
  python3 scripts/bench_opt_levels.py --benches=loop_sum,array_ops
  python3 scripts/bench_opt_levels.py --sample-ms=0 --no-rustc --no-swiftc

The default compiler is the hosted product, resolved by xu_host_seed.sh.
All Xu compilations use run_product_compiler.sh to isolate imports and caches.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench_crosslang import (  # noqa: E402
    BENCHES,
    COMPILE_ITERS,
    RunStats,
    _curve_slug,
    cross_src,
    median,
    parse_benches,
    peer_sources,
    ver_line,
    xu_src,
)
from bench_rusage import peak_rss_method, run_one, sparkline, write_curve_csv, write_rss_svg  # noqa: E402

BENCH_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("XU_ROOT", BENCH_ROOT.parent / "xu")).expanduser().resolve()
sys.path.insert(0, str(ROOT / "scripts"))
from product_compiler import resolve_product_compiler as resolve_hosted_compiler, PRODUCT_RUNNER as HOSTED_RUNNER, product_compile_argv
HOST_SEED_RESOLVER = ROOT / "scripts" / "xu_host_seed.sh"
PRODUCT_RUNNER = ROOT / "scripts" / "run_product_compiler.sh"
# Keep this alias explicit: the boundary checker and product consumers use
# the same seam name when auditing compiler invocations.
PRODUCT_COMPILER_RUNNER = PRODUCT_RUNNER
LANE = "product"
SNAPSHOT = BENCH_ROOT / "reports" / "bench_opt_levels.latest.txt"
GATE_BENCHES = "loop_sum,sha256_chain,sort_lcg,iface_sum,match_sum"
OPTS = (0, 1, 2, 3)
# Extra Xu cells (opt code, MIR -O, extra argv, label).
# 4 = --no-regcache; 12 = MIR-O1 + RA-O2; 21 = MIR-O2 + RA-O1.
XU_SPLIT = (
    (4, 1, ["--no-regcache"], "nrc"),
    (12, 1, ["--ra=2"], "m1r2"),
    (21, 2, ["--ra=1"], "m2r1"),
)
O3_OVER_O2_GATE = 1.1
# O2/O3 may not be slower than O1 by both 5% and 0.5ms (P50).
O2_OVER_O1_FRAC = 1.05
O2_OVER_O1_S = 0.0005
# Same-tier timeout vs default (O1): 5× median, at least 1s.
TIER_TIMEOUT_X = 5.0
# A deadlocked first anchor must not hold the entire suite indefinitely.
INITIAL_TIMEOUT_S = 60.0
# Short-bench wall ≫ in-process CPU: leftover lifecycle wait (was ~50ms poll).
WALL_OVER_CPU_S = 0.040
SHORT_CPU_S = 0.040
WALL_CPU_SKIP = frozenset({"chan_ping"})


def opt_label(opt: int) -> str:
    for code, _mir, _extra, lab in XU_SPLIT:
        if code == opt:
            return lab
    return f"O{opt}"

IMPL_XU = "xu"
IMPL_CLANG = "clang"
IMPL_GO = "go"
IMPL_RUSTC = "rustc"
IMPL_SWIFTC = "swiftc"
ALIAS_O1 = {IMPL_GO, IMPL_SWIFTC}


@dataclass
class Cell:
    stats: RunStats
    nbytes: int
    path: Path


def timed_interleaved(
    bins: dict[tuple[str, int], Path],
    iters: int,
    *,
    discard_first: bool,
    sample_interval_s: float | None,
    cwd: Path,
    expect: bytes,
    short_iters: int = 0,
    on_rounds=None,
) -> tuple[dict[tuple[str, int], RunStats], dict[tuple[str, int], str]]:
    """Measure each tier once per round, rotating and reversing run order.

    Contiguous tier batches confound thermal/host drift with optimization
    level. Warm every binary first, then interleave the same number of clean
    wall/CPU/wait4 samples. RSS polling remains a separate, untimed run.
    Retain any mismatching stdout, including warmup/curve runs, rather than
    accepting only the last iteration's output.
    """
    keys = sorted(bins, key=lambda key: (key != (IMPL_XU, 1), key))
    samples = {key: [] for key in keys}
    outputs: dict[tuple[str, int], bytes] = {}
    mismatches: set[tuple[str, int]] = set()
    errors: dict[tuple[str, int], str] = {}
    o1_s: float | None = None
    o1_cpu: float | None = None

    def take(key, interval=None):
        nonlocal o1_s
        timeout = INITIAL_TIMEOUT_S
        # Keep watchdog/thread overhead identical for measured Xu tiers.
        # Before the O1 anchor exists, use a bounded calibration deadline.
        if key[0] == IMPL_XU and o1_s is not None:
            timeout = max(o1_s * TIER_TIMEOUT_X, 1.0)
        s = run_one([str(bins[key])], sample_interval_s=interval,
                    timeout_s=timeout, cwd=cwd)
        if s.returncode != 0:
            if timeout is not None and s.wall_s >= timeout:
                errors[key] = f"TIMEOUT: {s.wall_s:.1f}s >= {timeout:.1f}s"
            else:
                diagnostic = (s.stderr or s.stdout).decode("utf-8", "replace")[-400:]
                errors[key] = f"run failed (exit {s.returncode}): " + diagnostic
            return None
        if key not in mismatches:
            outputs[key] = s.stdout
        if s.stdout != expect:
            mismatches.add(key)
        if key == (IMPL_XU, 1) and interval is None:
            previous = samples[key]
            o1_s = median([p.wall_s for p in previous] + [s.wall_s])
        return s

    if discard_first:
        for key in keys:
            anchor = take(key)
            if key == (IMPL_XU, 1) and anchor is not None:
                o1_cpu = anchor.cpu_s
    rounds = iters
    if o1_cpu is None or o1_cpu < SHORT_CPU_S:
        rounds = max(rounds, short_iters)
    if on_rounds is not None:
        on_rounds(rounds)
    for round_no in range(rounds):
        # Mirror the first half's rotated rounds in the second half. Each
        # pair sees opposite positions under host drift; an odd run count
        # has just one unpaired central round.
        mirror = min(round_no, rounds - 1 - round_no)
        offset = mirror % len(keys) if keys else 0
        order = keys[offset:] + keys[:offset]
        if round_no >= (rounds + 1) // 2:
            order.reverse()
        for key in order:
            if key in errors:
                continue
            sample = take(key)
            if sample is not None:
                samples[key].append(sample)
    result = {}
    for key in keys:
        if key in errors:
            continue
        curve = ()
        if sample_interval_s is not None and sample_interval_s > 0:
            sample = take(key, sample_interval_s)
            if sample is None:
                continue
            curve = sample.rss_curve
        row = samples[key]
        result[key] = RunStats(
            best_s=min(s.wall_s for s in row),
            med_s=median([s.wall_s for s in row]),
            med_rss_mib=median([s.max_rss_mib for s in row]),
            max_rss_mib=max(s.max_rss_mib for s in row),
            med_cpu_s=median([s.cpu_s for s in row]),
            stdout=outputs[key].decode("utf-8", "replace"), rss_curve=curve,
        )
    return result, errors


def sha12(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()[:12]


def is_executable(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def _absolute_candidate(value: str) -> Path:
    """Resolve a user-supplied path relative to the caller's cwd."""

    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    try:
        return path.resolve()
    except (OSError, RuntimeError) as exc:
        raise SystemExit(f"bench_opt_levels: cannot resolve compiler {value!r}: {exc}") from exc


def _lexical_candidate(value: str) -> Path:
    """Make a user path absolute while preserving symlink spelling."""

    return _lexical_path(Path(value))


def xu_compile_argv(compiler: Path, src: Path, opt: int, out: Path,
                    extra: list[str] | None = None, *, lane: str = LANE) -> list[str]:
    if lane != "product":
        raise ValueError(f"unsupported compiler lane: {lane}")
    return product_compile_argv(compiler, "build", str(src), f"-O{opt}",
                                *(extra or []), "-o", str(out), runner=PRODUCT_COMPILER_RUNNER)


def clang_compile_argv(clang: str, src: Path, opt: int, out: Path) -> list[str]:
    return [clang, f"-O{opt}", "-o", str(out), str(src)]


def go_compile_argv(go: str, src: Path, opt: int, out: Path) -> list[str]:
    sources = [str(src), *peer_sources(src.stem, "go")[1:]]
    if opt <= 0:
        return [go, "build", "-gcflags=all=-N -l", "-o", str(out), *sources]
    return [go, "build", "-o", str(out), *sources]


def rustc_compile_argv(rustc: str, src: Path, opt: int, out: Path) -> list[str]:
    return [rustc, "-C", f"opt-level={opt}", "-o", str(out), str(src)]


def swiftc_compile_argv(swiftc: str, src: Path, opt: int, out: Path) -> list[str]:
    flag = "-Onone" if opt <= 0 else "-O"
    # Match the cross-language driver: keep writable module caches beside
    # the temporary binaries and include shared software AES sources.
    sources = [str(src), *peer_sources(src.stem, "swift")[1:]]
    return [swiftc, "-module-cache-path", str(out.parent / "swift-module-cache"),
            flag, "-o", str(out), *sources]


def ensure_xupath() -> None:
    src = str(ROOT / "src")
    cur = os.environ.get("XUPATH", "")
    parts = [p for p in cur.split(":") if p]
    if src not in parts:
        os.environ["XUPATH"] = src if not cur else f"{src}:{cur}"


def resolve_compiler(explicit: str | None, lane: str = "product") -> Path:
    if lane != "product":
        raise ValueError(f"unsupported compiler lane: {lane}")
    return resolve_hosted_compiler(explicit)


def resolve_product_xu(explicit: str | None) -> Path:
    """Stable product-lane seam for callers and boundary audits."""

    return resolve_compiler(explicit, "product")


def fmt_pair(med_s: float, best_s: float) -> str:
    return f"{med_s * 1000.0:.1f} ({best_s * 1000.0:.1f})"


def speedup(base_s: float, other_s: float) -> str:
    if other_s <= 0:
        return "—"
    return f"{base_s / other_s:.2f}×"


def _clear_output(path: Path) -> None:
    """Remove a previous artifact so a failed compile cannot look successful."""

    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _artifact_ready(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def compile_one(cmd: list[str], out: Path) -> str | None:
    _clear_output(out)
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0 or not _artifact_ready(out):
        return (p.stderr or p.stdout or "no binary")[-400:].replace("\n", " ")
    out.chmod(out.stat().st_mode | stat.S_IEXEC)
    return None


def timed_compile(
    cmd: list[str],
    out: Path,
    *,
    iters: int,
    discard_first: bool,
) -> tuple[str | None, RunStats | None]:
    """Time an already-built compiler. Last successful run leaves `out`."""
    walls: list[float] = []
    rss: list[float] = []
    cpus: list[float] = []
    total = iters + (1 if discard_first else 0)
    for i in range(total):
        _clear_output(out)
        s = run_one(cmd, cwd=ROOT)
        if s.returncode != 0 or not _artifact_ready(out):
            err = (s.stderr or s.stdout).decode("utf-8", "replace")[-400:]
            return (err or "no binary").replace("\n", " "), None
        if discard_first and i == 0:
            continue
        walls.append(s.wall_s)
        rss.append(s.max_rss_mib)
        cpus.append(s.cpu_s)
    out.chmod(out.stat().st_mode | stat.S_IEXEC)
    # GetProcessTimes/PeakWorkingSetSize describe Bash itself on Windows,
    # not the compiler child launched by the hermetic product wrapper.
    # Keep end-to-end wall time; unavailable compiler metrics are not zero.
    if sys.platform == "win32" and len(cmd) > 1 and Path(cmd[1]) == PRODUCT_COMPILER_RUNNER:
        rss = [float("nan")]
        cpus = [float("nan")]
    return None, RunStats(
        best_s=min(walls),
        med_s=median(walls),
        med_rss_mib=median(rss),
        max_rss_mib=max(rss),
        med_cpu_s=median(cpus),
        stdout="",
    )


COMPILE_SECTION = "## compile wall median ms (already-built compiler)"


def splice_compile_section(path: Path, block: str, lane: str, xu_sha256: str, benches: str) -> None:
    from bench_snapshot_identity import require_identity
    require_identity(path, lane, xu_sha256, benches)
    prev = path.read_text() if path.is_file() else ""
    idx = prev.find("\n" + COMPILE_SECTION)
    if idx < 0:
        idx = prev.find(COMPILE_SECTION)
    if idx >= 0:
        prev = prev[:idx].rstrip() + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prev.rstrip() + "\n\n" + block.lstrip("\n"))


def check_stdout(outs: dict[int, bytes], expect: bytes) -> tuple[bool, str]:
    ref = outs.get(0) or outs.get(1)
    if ref is None:
        return False, "—"
    ok = ref == expect and all(data == ref for data in outs.values())
    return ok, sha12(ref)


def ratio_num(a: float | None, b: float | None) -> str:
    if a is None or b is None or b <= 0:
        return "—"
    return f"{a / b:.2f}×"


def cell_attr(row: dict[int, Cell], opt: int, attr: str) -> float | None:
    c = row.get(opt)
    if c is None:
        return None
    return float(getattr(c.stats, attr))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xu", help="compiler path (lane-specific; no implicit fallback)")
    ap.add_argument(
        "--lane",
        choices=("product",),
        default=LANE,
        help="hosted product compiler lane (default: product)",
    )
    ap.add_argument("--clang", default="clang")
    ap.add_argument("--go", default="go")
    ap.add_argument("--rustc", default="rustc")
    ap.add_argument("--swiftc", default="swiftc")
    ap.add_argument("--no-clang", action="store_true")
    ap.add_argument("--no-go", action="store_true")
    ap.add_argument("--no-rustc", action="store_true")
    ap.add_argument("--no-swiftc", action="store_true")
    ap.add_argument("--out", help="write report to this path")
    ap.add_argument("--save", action="store_true", help=f"write snapshot to {SNAPSHOT}")
    ap.add_argument(
        "--check",
        action="store_true",
        help="fail on Xu stdout MISMATCH, timeout, wall≫CPU wait, or O2/O3 slower than O1",
    )
    ap.add_argument("--quick", action="store_true", help=f"gate subset ({GATE_BENCHES})")
    ap.add_argument("--benches")
    ap.add_argument("--iters", type=int, default=7)
    ap.add_argument(
        "--compile-iters",
        type=int,
        default=COMPILE_ITERS,
        help=f"compile timing iters (default {COMPILE_ITERS})",
    )
    ap.add_argument(
        "--skip-runtime",
        action="store_true",
        help="compile timing only (keep previous runtime snapshot on --save)",
    )
    ap.add_argument(
        "--no-compile-times",
        action="store_true",
        help="compile once, do not report compile wall/RSS",
    )
    ap.add_argument("--discard-first", action="store_true", default=True)
    ap.add_argument("--no-discard-first", action="store_false", dest="discard_first")
    ap.add_argument(
        "--sample-ms",
        type=float,
        default=None,
        help="live RSS interval ms (default 5; 0=off; --check/--quick default 0)",
    )
    ap.add_argument("--curves-dir")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    if args.out:
        Path(args.out).expanduser().parent.mkdir(parents=True, exist_ok=True)
    if args.iters < 1:
        raise SystemExit("--iters must be >= 1")
    if args.compile_iters < 1:
        raise SystemExit("--compile-iters must be >= 1")

    if args.list:
        print(f"{'bench':<18} {'c':<4} {'go':<4} {'rs':<4} {'swift':<6} face")
        for b in BENCHES:
            print(
                f"{b.name:<18} "
                f"{'yes' if 'c' in b.langs else 'no':<4} "
                f"{'yes' if 'go' in b.langs else 'no':<4} "
                f"{'yes' if 'rs' in b.langs else 'no':<4} "
                f"{'yes' if 'swift' in b.langs else 'no':<6} "
                f"{b.face}"
            )
        return 0

    if args.quick and args.benches:
        raise SystemExit("use either --quick or --benches, not both")
    if args.quick:
        selected = parse_benches(GATE_BENCHES)
    elif args.benches:
        selected = parse_benches(args.benches)
    else:
        selected = list(BENCHES)

    gate = args.check or args.quick
    if gate:
        args.no_rustc = True
        args.no_swiftc = True
        args.no_clang = True
        args.no_go = True
        args.no_compile_times = True
        args.skip_runtime = False
        if args.check and not args.quick and not args.benches:
            selected = list(BENCHES)
    if args.sample_ms is None:
        args.sample_ms = 0.0 if (gate or args.skip_runtime) else 5.0
    if args.sample_ms < 0:
        raise SystemExit("--sample-ms must be >= 0")

    lane = args.lane
    compiler = resolve_product_xu(args.xu)

    def pick(flag: bool, name: str, arg: str) -> str | None:
        if flag:
            return None
        p = shutil.which(arg)
        if p is None:
            print(f"bench_opt_levels: {name} not found ({arg}); skipping", flush=True)
        return p

    clang_bin = pick(args.no_clang, "clang", args.clang)
    go_bin = pick(args.no_go, "go", args.go)
    rustc_bin = pick(args.no_rustc, "rustc", args.rustc)
    swiftc_bin = pick(args.no_swiftc, "swiftc", args.swiftc)

    tmp = Path(tempfile.mkdtemp(prefix="xu_opt_"))
    # Execute every implementation of a benchmark in the same private
    # directory. File-I/O benchmarks must never create or overwrite payloads
    # in the checkout merely because this script was launched from ROOT.
    run_dirs: dict[str, Path] = {}
    for bench in selected:
        run_dir = tmp / "run" / bench.name
        run_dir.mkdir(parents=True, exist_ok=True)
        run_dirs[bench.name] = run_dir
    lines: list[str] = []
    fail = 0
    mismatch_notes: list[str] = []

    def log(s: str = "") -> None:
        s = s.rstrip()
        print(s, flush=True)
        lines.append(s)

    host = f"{platform.platform()} {platform.machine()}"
    kind = "product"
    disc = "yes" if args.discard_first else "no"
    sample_s = None if args.sample_ms <= 0 else args.sample_ms / 1000.0
    out_path = Path(args.out) if args.out else (SNAPSHOT if args.save else None)
    curves_dir: Path | None = None
    if sample_s is not None:
        if args.curves_dir:
            curves_dir = Path(args.curves_dir)
        elif out_path is not None:
            curves_dir = Path(str(out_path) + ".curves")
        else:
            curves_dir = tmp / "curves"

    log(f"# bench_opt_levels — {time.strftime('%Y-%m-%d %H:%M')} host: {host}")
    from bench_snapshot_identity import compiler_sha256
    xu_sha256 = compiler_sha256(compiler)
    log(f"# lane: {lane}")
    log(f"# xu_sha256: {xu_sha256}")
    log(f"# xu: {compiler} ({kind})")
    if clang_bin:
        log(f"# clang: {ver_line([clang_bin, '--version'])}")
    else:
        log("# clang: skipped")
    if go_bin:
        log(f"# go: {ver_line([go_bin, 'version'])}")
        log("# go tiers: O0 = -gcflags=all=-N -l; O1=O2=O3 = go build default")
    else:
        log("# go: skipped")
    if rustc_bin:
        log(f"# rustc: {ver_line([rustc_bin, '--version'])}")
    else:
        log("# rustc: skipped")
    if swiftc_bin:
        log(f"# swiftc: {ver_line([swiftc_bin, '--version'])}")
        log("# swiftc tiers: O0 = -Onone; O1=O2=O3 = -O")
    else:
        log("# swiftc: skipped")
    log(
        f"# run: requested {args.iters} rounds discard-first={disc}; "
        "median peak RSS + CPU(user+sys); binary size; ratios use median"
    )
    log("# sampling: warm all tiers, interleave rounds with rotating/reversed order; RSS curve runs separate")
    if gate:
        log("# gate sampling: minimum 21 rounds when warmed O1 CPU <40ms (or calibration unavailable); thresholds unchanged")
    if args.no_compile_times:
        log("# compile timing: off (single untimed compile)")
    else:
        log(
            f"# compile: best+median of {args.compile_iters} discard-first={disc}; "
            "compiler peak RSS + CPU (wait4 parent; rustc/swiftc children may be undercounted)"
        )
        if sys.platform == "win32":
            log("# Xu compile CPU/RSS: nan = unavailable through the Bash wrapper; wall includes wrapper overhead")
    if args.skip_runtime:
        log("# runtime: skipped")
    if sample_s is None:
        log("# curves: disabled")
    else:
        log(f"# curves: live RSS every {args.sample_ms:g}ms → {curves_dir}")
    log(
        "# method: plb2-style whole-program wall; AOT; same-algorithm ports; "
        f"RSS peak={peak_rss_method()}; curve=live poll"
    )
    log(f"# benches: {', '.join(b.name for b in selected)}")
    log(
        f"# opts: {', '.join(f'-O{o}' for o in OPTS)}"
        " + --no-regcache + -O1 --ra=2 + -O2 --ra=1 (Xu)"
    )
    log("")

    table: dict[str, dict[str, dict[int, Cell]]] = {
        IMPL_XU: {},
        IMPL_CLANG: {},
        IMPL_GO: {},
        IMPL_RUSTC: {},
        IMPL_SWIFTC: {},
    }
    impls_order = [IMPL_XU]
    if clang_bin:
        impls_order.append(IMPL_CLANG)
    if go_bin:
        impls_order.append(IMPL_GO)
    if rustc_bin:
        impls_order.append(IMPL_RUSTC)
    if swiftc_bin:
        impls_order.append(IMPL_SWIFTC)

    curves_by_bench: dict[str, dict[str, tuple]] = {}
    ctable: dict[str, dict[str, dict[int, RunStats]]] = {
        IMPL_XU: {},
        IMPL_CLANG: {},
        IMPL_GO: {},
        IMPL_RUSTC: {},
        IMPL_SWIFTC: {},
    }

    def record_compile(impl: str, bench_name: str, opt: int, st: RunStats) -> None:
        ctable[impl].setdefault(bench_name, {})[opt] = st

    def do_compile(impl: str, bench_name: str, opt: int, cmd: list[str], out: Path) -> bool:
        if args.no_compile_times:
            err = compile_one(cmd, out)
            st = None
        else:
            err, st = timed_compile(
                cmd,
                out,
                iters=args.compile_iters,
                discard_first=args.discard_first,
            )
        if err:
            log(f"  compile FAIL {impl} {opt_label(opt)} {bench_name}: {err}")
            return False
        add_bin(impl, opt, out)
        if st is not None:
            record_compile(impl, bench_name, opt, st)
        return True

    if not args.skip_runtime:
        log("## runtime + resources + binary size")
        log(
            f"{'bench':<18} {'impl':<8} {'opt':<4} "
            f"{'best_ms':>8} {'med_ms':>8} {'rss_mib':>8} {'cpu_ms':>8} "
            f"{'bytes':>10}  stdout"
        )
        log("")

    for bench in selected:
        expect = bench.expect.encode("utf-8")
        bins: dict[tuple[str, int], Path] = {}

        def add_bin(impl: str, opt: int, path: Path) -> None:
            bins[(impl, opt)] = path

        src_xu = xu_src(bench.name)
        if not src_xu.is_file():
            log(f"{bench.name:<18} {IMPL_XU:<8}  MISSING {src_xu}")
            fail = 1
            continue
        for opt in OPTS:
            out = tmp / f"xu_{bench.name}.O{opt}.xin"
            if not do_compile(
                IMPL_XU,
                bench.name,
                opt,
                xu_compile_argv(compiler, src_xu, opt, out, lane=lane),
                out,
            ):
                fail = 1
        for code, mir, extra, lab in XU_SPLIT:
            out = tmp / f"xu_{bench.name}.{lab}.xin"
            cmd = xu_compile_argv(
                compiler,
                src_xu,
                mir,
                out,
                extra=list(extra),
                lane=lane,
            )
            if not do_compile(IMPL_XU, bench.name, code, cmd, out):
                fail = 1

        def try_lang(
            impl: str,
            lang: str,
            ext: str,
            tool: str | None,
            argv_fn,
            opts: tuple[int, ...],
        ) -> None:
            if tool is None or lang not in bench.langs:
                return
            src = cross_src(bench.name, ext)
            if not src.is_file():
                log(f"  skip {impl} {bench.name}: no {src}")
                return
            for opt in opts:
                suffix = ".exe" if sys.platform == "win32" else ""
                out = tmp / f"{impl}_{bench.name}.O{opt}{suffix}"
                do_compile(impl, bench.name, opt, argv_fn(tool, src, opt, out), out)

        try_lang(IMPL_CLANG, "c", "c", clang_bin, clang_compile_argv, OPTS)
        try_lang(IMPL_GO, "go", "go", go_bin, go_compile_argv, (0, 1))
        try_lang(IMPL_RUSTC, "rs", "rs", rustc_bin, rustc_compile_argv, OPTS)
        try_lang(IMPL_SWIFTC, "swift", "swift", swiftc_bin, swiftc_compile_argv, (0, 1))

        for impl in ALIAS_O1:
            row = ctable[impl].get(bench.name, {})
            if 1 in row:
                row[2] = row[1]
                row[3] = row[1]

        if args.skip_runtime:
            continue

        run_opts = list(OPTS)
        for code, _mir, _extra, _lab in XU_SPLIT:
            if (IMPL_XU, code) in bins:
                run_opts.append(code)
        run_bins = {key: path for key, path in bins.items()
                    if key[1] in run_opts and key[0] in impls_order}
        measured, errors = timed_interleaved(
            run_bins, args.iters, discard_first=args.discard_first,
            sample_interval_s=sample_s, cwd=run_dirs[bench.name], expect=expect,
            short_iters=21 if gate else 0,
            on_rounds=lambda count: log(f"# {bench.name}: {count} measured rounds per tier"),
        )
        for (impl, opt), error in errors.items():
            log(f"  run FAIL {impl} {opt_label(opt)} {bench.name}: {error}")
            if impl == IMPL_XU:
                fail = 1
        for (impl, opt), stats in measured.items():
            path = run_bins[(impl, opt)]
            table[impl].setdefault(bench.name, {})[opt] = Cell(
                stats=stats, nbytes=path.stat().st_size, path=path,
            )
            if stats.rss_curve:
                label = f"{impl} -O{opt}"
                curves_by_bench.setdefault(bench.name, {})[label] = stats.rss_curve
                if curves_dir is not None:
                    write_curve_csv(
                        curves_dir / f"{bench.name}__{_curve_slug(label)}.csv",
                        stats.rss_curve,
                    )

        for impl in ALIAS_O1:
            row = table[impl].get(bench.name, {})
            if 1 in row:
                row[2] = row[1]
                row[3] = row[1]

        for impl in impls_order:
            row = table[impl].get(bench.name, {})
            if impl != IMPL_XU and not row:
                continue
            keys = list(OPTS) + (
                [c for c, *_ in XU_SPLIT if c in row] if impl == IMPL_XU else []
            )
            outs = {
                opt: row[opt].stats.stdout.encode("utf-8")
                for opt in keys
                if opt in row
            }
            ok, sha = check_stdout(outs, expect)
            if not ok:
                mismatch_notes.append(f"{impl} {bench.name}")
                if impl == IMPL_XU:
                    fail = 1
            printed = set()
            for opt in keys:
                c = row.get(opt)
                if c is None:
                    if impl == IMPL_XU:
                        log(f"{bench.name:<18} {impl:<8} O{opt:<3} {'FAIL':>8}")
                    continue
                if id(c) in printed:
                    continue
                printed.add(id(c))
                # Keep the aggregate failure, but identify the tier whose
                # output differs instead of marking every tier as wrong.
                data = outs[opt]
                status = f"OK {sha12(data)}" if data == expect else "MISMATCH"
                spark = sparkline(c.stats.rss_curve) if c.stats.rss_curve else ""
                extra = f"  {spark}" if spark else ""
                note = " (=O1)" if impl in ALIAS_O1 and opt == 1 else ""
                olabel = opt_label(opt)
                wait_ms = (c.stats.med_s - c.stats.med_cpu_s) * 1000.0
                wait = f" wait={wait_ms:+.1f}ms" if wait_ms > 15.0 else ""
                log(
                    f"{bench.name:<18} {impl:<8} {olabel:<4} "
                    f"{c.stats.best_s * 1000:8.1f} {c.stats.med_s * 1000:8.1f} "
                    f"{c.stats.med_rss_mib:8.2f} {c.stats.med_cpu_s * 1000:8.1f} "
                    f"{c.nbytes:10d}  {status}{note}{extra}{wait}"
                )

    def emit_pivot(title: str, fmt, src: dict) -> None:
        log("")
        log(f"## {title}")
        log(
            f"{'bench':<18} {'impl':<8} "
            f"{'O0':>10} {'O1':>10} {'O2':>10} {'O3':>10}"
        )
        for bench in selected:
            for impl in impls_order:
                row = src[impl].get(bench.name, {})
                if not row:
                    continue
                cells = [fmt(row.get(o)) for o in OPTS]
                log(
                    f"{bench.name:<18} {impl:<8} "
                    f"{cells[0]:>10} {cells[1]:>10} {cells[2]:>10} {cells[3]:>10}"
                )

    def wall_cell(c: Cell | None) -> str:
        return "—" if c is None else f"{c.stats.med_s * 1000:.1f}"

    def rss_cell(c: Cell | None) -> str:
        return "—" if c is None else f"{c.stats.med_rss_mib:.2f}"

    def cpu_cell(c: Cell | None) -> str:
        return "—" if c is None else f"{c.stats.med_cpu_s * 1000:.1f}"

    def bytes_cell(c: Cell | None) -> str:
        return "—" if c is None else str(c.nbytes)

    def ct_wall(s: RunStats | None) -> str:
        return "—" if s is None else f"{s.med_s * 1000:.1f}"

    def ct_best(s: RunStats | None) -> str:
        return "—" if s is None else f"{s.best_s * 1000:.1f}"

    def ct_rss(s: RunStats | None) -> str:
        return "—" if s is None else f"{s.med_rss_mib:.1f}"

    def ct_cpu(s: RunStats | None) -> str:
        return "—" if s is None else f"{s.med_cpu_s * 1000:.1f}"

    def emit_xu_over(
        peer: str,
        peer_impl: str,
        title: str,
        attr: str,
        src: dict,
        cell_get,
    ) -> None:
        log("")
        log(f"## Xu / {peer} {title} (>1 Xu higher)")
        log(f"{'bench':<18} {'O0':>8} {'O1':>8} {'O2':>8} {'O3':>8}")
        for bench in selected:
            xu_row = src[IMPL_XU].get(bench.name, {})
            other = src[peer_impl].get(bench.name, {})
            if not other:
                log(f"{bench.name:<18} {'—':>8} {'—':>8} {'—':>8} {'—':>8}")
                continue
            log(
                f"{bench.name:<18} "
                f"{ratio_num(cell_get(xu_row, 0, attr), cell_get(other, 0, attr)):>8} "
                f"{ratio_num(cell_get(xu_row, 1, attr), cell_get(other, 1, attr)):>8} "
                f"{ratio_num(cell_get(xu_row, 2, attr), cell_get(other, 2, attr)):>8} "
                f"{ratio_num(cell_get(xu_row, 3, attr), cell_get(other, 3, attr)):>8}"
            )

    def ct_attr(row: dict[int, RunStats], opt: int, attr: str) -> float | None:
        s = row.get(opt)
        if s is None:
            return None
        return float(getattr(s, attr))

    if not args.skip_runtime:
        emit_pivot("wall median ms", wall_cell, table)
        emit_pivot("peak RSS median MiB (wait4 ru_maxrss)", rss_cell, table)
        emit_pivot("CPU median ms (user+sys)", cpu_cell, table)
        emit_pivot("binary bytes", bytes_cell, table)

        for impl, name in (
            (IMPL_CLANG, "clang"),
            (IMPL_GO, "go"),
            (IMPL_RUSTC, "rustc"),
            (IMPL_SWIFTC, "swiftc"),
        ):
            if impl not in impls_order:
                continue
            emit_xu_over(name, impl, "wall (median)", "med_s", table, cell_attr)
            emit_xu_over(name, impl, "RSS (median MiB)", "med_rss_mib", table, cell_attr)
            emit_xu_over(name, impl, "CPU (median)", "med_cpu_s", table, cell_attr)

        log("")
        log("## speedup vs own -O0 (median wall; >1 faster than own O0)")
        log(f"{'bench':<18} {'impl':<8} {'O1':>8} {'O2':>8} {'O3':>8}")
        for bench in selected:
            for impl in impls_order:
                row = table[impl].get(bench.name, {})
                base = row.get(0)
                if base is None:
                    continue

                def sp(opt: int, r=row, b=base) -> str:
                    c = r.get(opt)
                    return "—" if c is None else speedup(b.stats.med_s, c.stats.med_s)

                log(f"{bench.name:<18} {impl:<8} {sp(1):>8} {sp(2):>8} {sp(3):>8}")

        if curves_dir is not None and curves_by_bench:
            log("")
            log("## RSS curves")
            curves_dir.mkdir(parents=True, exist_ok=True)
            for bench_name, series in curves_by_bench.items():
                svg = curves_dir / f"{bench_name}.svg"
                write_rss_svg(svg, series, title=f"{bench_name} RSS over time")
                log(f"  {svg}  ({len(series)} series)")

        ls = table[IMPL_XU].get("loop_sum", {})
        c2, c3 = ls.get(2), ls.get(3)
        if c2 is not None and c3 is not None:
            ms2 = c2.stats.med_s * 1000.0
            ms3 = c3.stats.med_s * 1000.0
            log("")
            log(
                f"loop_sum xu O2 med={ms2:.1f}ms (best {c2.stats.best_s * 1000:.1f})  "
                f"O3 med={ms3:.1f}ms (best {c3.stats.best_s * 1000:.1f})  "
                f"(gate: O3 median <= O2 × {O3_OVER_O2_GATE})"
            )
            if args.check and ms3 > ms2 * O3_OVER_O2_GATE:
                log(
                    f"  REGRESSION: loop_sum O3 {ms3:.1f}ms > O2 {ms2:.1f}ms "
                    f"×{O3_OVER_O2_GATE}"
                )
                fail = 1
        elif args.check and any(b.name == "loop_sum" for b in selected):
            log("  REGRESSION: loop_sum O2/O3 timings missing")
            fail = 1

        if args.check:
            log("")
            log(
                f"# O2/O3 vs O1 (all benches): "
                f"P50 must not exceed O1 by {O2_OVER_O1_FRAC}× "
                f"and {O2_OVER_O1_S * 1000:.1f}ms"
            )
            log(
                f"# wall vs CPU: extra >{WALL_OVER_CPU_S * 1000:.0f}ms idle "
                f"when CPU <{SHORT_CPU_S * 1000:.0f}ms fails "
                f"(skip {', '.join(sorted(WALL_CPU_SKIP))})"
            )
            for bench in selected:
                row = table[IMPL_XU].get(bench.name, {})
                c1 = row.get(1)
                if c1 is not None:
                    for opt in (2, 3):
                        cx = row.get(opt)
                        if cx is None:
                            continue
                        o1 = c1.stats.med_s
                        ox = cx.stats.med_s
                        if ox > o1 * O2_OVER_O1_FRAC and (ox - o1) > O2_OVER_O1_S:
                            log(
                                f"  REGRESSION: {bench.name} {opt_label(opt)} "
                                f"{ox * 1000:.1f}ms > O1 {o1 * 1000:.1f}ms "
                                f"(+{(ox / o1 - 1) * 100:.1f}%)"
                            )
                            fail = 1
                if bench.name in WALL_CPU_SKIP:
                    continue
                keys = list(OPTS) + [c for c, *_ in XU_SPLIT if c in row]
                for opt in keys:
                    cx = row.get(opt)
                    if cx is None:
                        continue
                    wall = cx.stats.med_s
                    cpu = cx.stats.med_cpu_s
                    if cpu < SHORT_CPU_S and wall > cpu + WALL_OVER_CPU_S:
                        log(
                            f"  REGRESSION: {bench.name} {opt_label(opt)} "
                            f"wall {wall * 1000:.1f}ms vs CPU {cpu * 1000:.1f}ms "
                            f"(+{(wall - cpu) * 1000:.1f}ms idle)"
                        )
                        fail = 1

        if mismatch_notes:
            log("")
            log("# stdout mismatches: " + ", ".join(mismatch_notes))

    compile_start = len(lines)
    if not args.no_compile_times:
        log("")
        log(
            f"{COMPILE_SECTION}  "
            f"best+median of {args.compile_iters} discard-first={disc}"
        )
        log(
            f"{'bench':<18} {'impl':<8} {'opt':<4} "
            f"{'best_ms':>8} {'med_ms':>8} {'rss_mib':>8} {'cpu_ms':>8}"
        )
        for bench in selected:
            for impl in impls_order:
                row = ctable[impl].get(bench.name, {})
                if not row:
                    continue
                printed = set()
                for opt in OPTS:
                    s = row.get(opt)
                    if s is None:
                        continue
                    if id(s) in printed:
                        continue
                    printed.add(id(s))
                    note = " (=O1)" if impl in ALIAS_O1 and opt == 1 else ""
                    log(
                        f"{bench.name:<18} {impl:<8} O{opt:<3} "
                        f"{s.best_s * 1000:8.1f} {s.med_s * 1000:8.1f} "
                        f"{s.med_rss_mib:8.1f} {s.med_cpu_s * 1000:8.1f}{note}"
                    )
        emit_pivot(COMPILE_SECTION[3:], ct_wall, ctable)
        emit_pivot("compile best ms", ct_best, ctable)
        emit_pivot("compile peak RSS median MiB (compiler process)", ct_rss, ctable)
        emit_pivot("compile CPU median ms (user+sys)", ct_cpu, ctable)
        for impl, name in (
            (IMPL_CLANG, "clang"),
            (IMPL_GO, "go"),
            (IMPL_RUSTC, "rustc"),
            (IMPL_SWIFTC, "swiftc"),
        ):
            if impl not in impls_order:
                continue
            emit_xu_over(
                name, impl, "compile wall (median)", "med_s", ctable, ct_attr
            )
            emit_xu_over(
                name, impl, "compile RSS (median MiB)", "med_rss_mib", ctable, ct_attr
            )

    compile_block = "\n".join(lines[compile_start:]).lstrip("\n")
    text = "\n".join(lines) + "\n"
    if args.skip_runtime and args.save:
        splice_compile_section(SNAPSHOT, compile_block, lane, xu_sha256, ", ".join(b.name for b in selected))
        print(f"# spliced compile section into {SNAPSHOT}", flush=True)
        if args.out:
            po = Path(args.out)
            po.parent.mkdir(parents=True, exist_ok=True)
            po.write_text(text)
            print(f"# wrote {po}", flush=True)
    elif out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text)
        print(f"# wrote {out_path}", flush=True)

    return 1 if args.check and fail else 0


if __name__ == "__main__":
    sys.exit(main())
