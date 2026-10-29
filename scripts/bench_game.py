#!/usr/bin/env python3
"""Benchmarks Game suite: Xu vs C / C++ / Rust / Go.

Single-thread, same algorithm, official small-N golden stdout plus an untimed
streaming SHA-256/length equality gate at the N used for performance runs.
Method: whole-program wall; report best + median wall, median peak RSS + CPU;
ratios use median. Optional --discard-first. Not CLBG peak-golf (no SIMD / OpenMP).

Usage:
  python3 scripts/bench_game.py --verify-only
  python3 scripts/bench_game.py --xu /path/to/xu --verify-only
  python3 scripts/bench_game.py --out docs/audit/bench_game.latest.txt
  python3 scripts/bench_game.py --benches=nbody,spectralnorm --quick
  python3 scripts/bench_game.py --out /tmp/g.txt --discard-first
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench_rusage import (  # noqa: E402
    run_one,
    sparkline,
    write_curve_csv,
    write_rss_svg,
)

BENCH_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("XU_ROOT", BENCH_ROOT.parent / "xu")).expanduser().resolve()
sys.path.insert(0, str(ROOT / "scripts"))
from product_compiler import resolve_product_compiler as resolve_hosted_compiler, PRODUCT_RUNNER as HOSTED_RUNNER, product_compile_argv
GAME = BENCH_ROOT / "tests" / "bench" / "game"
CROSS = GAME / "cross"
GOLDEN = GAME / "golden"
HOST_SEED_RESOLVER = ROOT / "scripts" / "xu_host_seed.sh"
PRODUCT_RUNNER = ROOT / "scripts" / "run_product_compiler.sh"
PRODUCT_COMPILER_RUNNER = PRODUCT_RUNNER
LANE = "product"

RUN_ITERS = 5
HASH_CHUNK_BYTES = 64 * 1024
REFERENCE_LANGS = ("c", "cc", "rs", "go", "xu")
QUICK_PERF_N = {
    "nbody": 500_000,
    "fannkuchredux": 10,
    "spectralnorm": 500,
    "mandelbrot": 1000,
    "fasta": 250_000,
    "binarytrees": 14,
}


def median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        raise ValueError("empty samples")
    mid = n // 2
    if n % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


@dataclass(frozen=True)
class PerfStats:
    best_s: float
    med_s: float
    med_rss_mib: float
    med_cpu_s: float
    rss_curve: tuple[tuple[float, float], ...] = ()


@dataclass(frozen=True)
class StdoutFingerprint:
    length: int
    sha256: str


@dataclass(frozen=True)
class Bench:
    name: str
    face: str
    verify_n: int
    perf_n: int
    golden: str
    binary: bool = False


BENCHES: list[Bench] = [
    Bench("nbody", "f64 多体", 1000, 5_000_000, "nbody-output.txt"),
    Bench("fannkuchredux", "整数置换", 7, 12, "fannkuchredux-output.txt"),
    Bench("spectralnorm", "f64 幂迭代", 100, 5500, "spectralnorm-output.txt"),
    Bench("mandelbrot", "PBM 位图", 200, 4000, "mandelbrot-output.txt", binary=True),
    Bench("fasta", "LCG+写出", 1000, 2_500_000, "fasta-output.txt"),
    Bench("binarytrees", "分配压力", 10, 18, "binarytrees-output.txt"),
]

BY_NAME = {b.name: b for b in BENCHES}
LANGS = ("xu", "c", "cc", "rs", "go")


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, **kw)


def which(name: str) -> str | None:
    return shutil.which(name)


def ver_line(cmd: list[str]) -> str:
    p = run(cmd, text=True)
    s = (p.stdout or p.stderr or "").strip().splitlines()
    return s[0] if s else "?"


def parse_benches(s: str | None) -> list[Bench]:
    if not s:
        return list(BENCHES)
    out = []
    for part in s.split(","):
        name = part.strip()
        if not name:
            continue
        if name not in BY_NAME:
            raise SystemExit(f"unknown bench {name!r}; known: {', '.join(BY_NAME)}")
        out.append(BY_NAME[name])
    if not out:
        raise SystemExit("empty --benches")
    return out


def resolve_product_xu(explicit: str | None) -> Path:
    return resolve_hosted_compiler(explicit)


def golden_bytes(b: Bench) -> bytes:
    return (GOLDEN / b.golden).read_bytes()


def perf_n_for(bench: Bench, quick: bool) -> int:
    return QUICK_PERF_N.get(bench.name, bench.perf_n) if quick else bench.perf_n


def _file_tail(f, limit: int) -> bytes:
    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(max(0, size - limit), os.SEEK_SET)
    return f.read()


def stdout_fingerprint(bin_path: Path, n: int) -> StdoutFingerprint:
    """Run once and hash stdout incrementally without retaining full output.

    This is deliberately separate from ``timed_perf`` so hashing cost can never
    enter a timing sample. bench_game currently configures no process timeout;
    this helper preserves that behavior and the existing non-zero-exit
    diagnostic (the final 200 stderr bytes).
    """
    digest = hashlib.sha256()
    length = 0
    with tempfile.SpooledTemporaryFile(max_size=256 * 1024) as err_f:
        process = subprocess.Popen(
            [str(bin_path), str(n)],
            stdout=subprocess.PIPE,
            stderr=err_f,
        )
        assert process.stdout is not None
        try:
            while True:
                chunk = process.stdout.read(HASH_CHUNK_BYTES)
                if not chunk:
                    break
                digest.update(chunk)
                length += len(chunk)
        except BaseException:
            process.kill()
            process.wait()
            raise
        finally:
            process.stdout.close()
        returncode = process.wait()
        if returncode != 0:
            stderr_tail = _file_tail(err_f, 200)
            raise RuntimeError(f"run failed {bin_path} {n}: {stderr_tail!r}")
    return StdoutFingerprint(length=length, sha256=digest.hexdigest())


def verify_full_stdout(
    bench: Bench,
    bins: dict[tuple[str, str], Path],
    n: int,
    log,
) -> bool:
    """Fingerprint each available implementation once and compare to a peer.

    Prefer C as the independent reference, then C++/Rust/Go; Xu is a fallback
    only for tool-limited hosts. The reference run is reused, not executed a
    second time.
    """
    available = [lang for lang in LANGS if (lang, bench.name) in bins]
    if not available:
        log(f"  SKIP     {bench.name} N={n} (no binaries)")
        return True
    reference = next(lang for lang in REFERENCE_LANGS if lang in available)
    order = [reference] + [lang for lang in available if lang != reference]
    expected: StdoutFingerprint | None = None
    ok = True
    for lang in order:
        got = stdout_fingerprint(bins[(lang, bench.name)], n)
        if expected is None:
            expected = got
            log(
                f"  REF  {lang:<3} {bench.name} N={n} "
                f"{got.length}B sha256={got.sha256}"
            )
        elif got == expected:
            log(
                f"  OK   {lang:<3} {bench.name} N={n} "
                f"{got.length}B sha256={got.sha256}"
            )
        else:
            ok = False
            log(
                f"  FAIL {lang:<3} {bench.name} N={n} "
                f"got={got.length}B/{got.sha256} "
                f"want={reference}:{expected.length}B/{expected.sha256}"
            )
    if len(available) == 1:
        log(
            f"  WARN     {bench.name} N={n}: only {reference} available; "
            "no cross-implementation comparison"
        )
    return ok


def compile_one(
    lang: str,
    bench: Bench,
    tmp: Path,
    tools: dict,
    xu_bin: Path,
    *,
    lane: str,
) -> Path | None:
    suffix = ".exe" if sys.platform == "win32" else ""
    out = tmp / f"{lang}_{bench.name}{suffix}"
    if lang == "xu":
        src = str(GAME / f"{bench.name}.xu")
        if lane != "product":
            raise ValueError(f"unsupported compiler lane: {lane}")
        cmd = product_compile_argv(xu_bin, "build", src, "-o", str(out), runner=PRODUCT_RUNNER)
    elif lang == "c":
        clang = tools.get("clang")
        if not clang:
            return None
        cmd = [clang, "-O3", "-o", str(out), str(CROSS / f"{bench.name}.c"), "-lm"]
    elif lang == "cc":
        cxx = tools.get("cxx")
        if not cxx:
            return None
        cmd = [cxx, "-O3", "-o", str(out), str(CROSS / f"{bench.name}.cc"), "-lm"]
    elif lang == "rs":
        rustc = tools.get("rustc")
        if not rustc:
            return None
        cmd = [
            rustc,
            "-C",
            "opt-level=3",
            "-o",
            str(out),
            str(CROSS / f"{bench.name}.rs"),
        ]
    elif lang == "go":
        go = tools.get("go")
        if not go:
            return None
        cmd = ["go", "build", "-o", str(out), str(CROSS / f"{bench.name}.go")]
    else:
        return None
    p = run(cmd, text=True)
    if p.returncode != 0:
        err = (p.stderr or p.stdout or "")[-500:]
        print(f"  compile FAIL {lang} {bench.name}: {err}", flush=True)
        return None
    os.chmod(out, 0o755)
    return out


def run_n(bin_path: Path, n: int, binary: bool) -> tuple[bytes, float]:
    s = run_one([str(bin_path), str(n)])
    if s.returncode != 0:
        raise RuntimeError(
            f"run failed {bin_path} {n}: {s.stderr[-200:]!r}"
        )
    return s.stdout, s.wall_s


def timed_perf(
    bin_path: Path,
    n: int,
    binary: bool,
    iters: int,
    discard_first: bool,
    sample_interval_s: float | None = None,
) -> PerfStats:
    """Timing runs without sampling; one extra run for RSS curve if requested."""
    walls: list[float] = []
    rss: list[float] = []
    cpus: list[float] = []
    total = iters + (1 if discard_first else 0)
    for i in range(total):
        s = run_one([str(bin_path), str(n)], sample_interval_s=None)
        if s.returncode != 0:
            raise RuntimeError(
                f"run failed {bin_path} {n}: {s.stderr[-200:]!r}"
            )
        if discard_first and i == 0:
            continue
        walls.append(s.wall_s)
        rss.append(s.max_rss_mib)
        cpus.append(s.cpu_s)
    curve: tuple[tuple[float, float], ...] = ()
    if sample_interval_s is not None and sample_interval_s > 0:
        cs = run_one(
            [str(bin_path), str(n)], sample_interval_s=sample_interval_s
        )
        if cs.returncode != 0:
            raise RuntimeError(
                f"curve run failed {bin_path} {n}: {cs.stderr[-200:]!r}"
            )
        curve = cs.rss_curve
    return PerfStats(
        best_s=min(walls),
        med_s=median(walls),
        med_rss_mib=median(rss),
        med_cpu_s=median(cpus),
        rss_curve=curve,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--xu",
        help="Xu compiler under test (product lane by default)",
    )
    ap.add_argument(
        "--lane",
        choices=("product",),
        default="product",
        help="hosted product compiler lane",
    )
    ap.add_argument("--out", help="write timing table here")
    ap.add_argument("--report", help="also write markdown report path")
    ap.add_argument("--benches", help="comma-separated subset")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument(
        "--quick",
        action="store_true",
        help="use smaller perf N (faster smoke)",
    )
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--iters", type=int, default=RUN_ITERS)
    ap.add_argument(
        "--discard-first",
        action="store_true",
        help="run once untimed before sampling (drop cold-cache first hit)",
    )
    ap.add_argument(
        "--sample-ms",
        type=float,
        default=5.0,
        help="live RSS sample interval in ms (0=disable curves; default 5)",
    )
    ap.add_argument(
        "--curves-dir",
        help="write RSS CSV+SVG curves here (default: <out>.curves/)",
    )
    args = ap.parse_args()
    if args.report:
        Path(args.report).expanduser().parent.mkdir(parents=True, exist_ok=True)
    if args.out:
        Path(args.out).expanduser().parent.mkdir(parents=True, exist_ok=True)
    if args.iters < 1:
        raise SystemExit("--iters must be >= 1")
    if args.sample_ms < 0:
        raise SystemExit("--sample-ms must be >= 0")

    lane = args.lane
    xu_bin = resolve_product_xu(args.xu)
    if not PRODUCT_COMPILER_RUNNER.is_file():
        raise SystemExit(
            f"bench_game: missing product compiler wrapper: {PRODUCT_COMPILER_RUNNER}"
        )

    if args.list:
        print(f"{'bench':<16} {'verify':>7} {'perf':>8}  face")
        for b in BENCHES:
            print(f"{b.name:<16} {b.verify_n:7d} {b.perf_n:8d}  {b.face}")
        return

    selected = parse_benches(args.benches)
    tools = {
        "clang": which("clang"),
        "cxx": which("clang++") or which("g++"),
        "rustc": which("rustc"),
        "go": which("go"),
    }
    tmp = Path(tempfile.mkdtemp(prefix="xu_game_"))
    lines: list[str] = []

    def log(s: str = ""):
        print(s, flush=True)
        lines.append(s)

    host = run(["uname", "-sm"], text=True).stdout.strip()
    log(f"# host: {host}")
    log(f"# date: {time.strftime('%Y-%m-%d %H:%M')}")
    log(f"# lane: {lane}")
    log(f"# xu: {xu_bin}")
    log("# suite: Benchmarks Game Wave1 (single-thread; Xu/C/C++/Rust/Go)")
    disc = "yes" if args.discard_first else "no"
    sample_s = None if args.sample_ms <= 0 else args.sample_ms / 1000.0
    log(
        f"# method: wall best+median of {args.iters}; discard-first={disc}; "
        "median peak RSS + CPU(user+sys); ratios use median; "
        "same-algorithm (no SIMD/OpenMP golf); RSS peak=wait4; "
        "curve=live poll; before timing, perf-N stdout=untimed streaming "
        "SHA-256+length"
    )
    if sample_s is None:
        log("# curves: disabled (--sample-ms=0)")
    else:
        log(f"# curves: live RSS every {args.sample_ms:g}ms")
    log(f"# benches: {', '.join(b.name for b in selected)}")
    if tools["clang"]:
        log(f"# clang: {ver_line(['clang', '--version'])}")
    if tools["cxx"]:
        log(f"# cxx: {ver_line([tools['cxx'], '--version'])}")
    if tools["rustc"]:
        log(f"# rustc: {ver_line(['rustc', '--version'])}")
    if tools["go"]:
        log(f"# go: {ver_line(['go', 'version'])}")
    log("")

    # compile all
    bins: dict[tuple[str, str], Path] = {}
    log("## compile")
    for b in selected:
        for lang in LANGS:
            p = compile_one(lang, b, tmp, tools, xu_bin, lane=lane)
            if p:
                bins[(lang, b.name)] = p
                log(f"  ok {lang:<3} {b.name}")
            else:
                log(f"  skip/fail {lang:<3} {b.name}")
    log("")

    # verify
    log("## verify (golden)")
    verify_ok = True
    for b in selected:
        want = golden_bytes(b)
        for lang in LANGS:
            key = (lang, b.name)
            if key not in bins:
                log(f"  SKIP {lang:<3} {b.name}")
                continue
            got, _ = run_n(bins[key], b.verify_n, b.binary)
            if got == want:
                log(f"  OK   {lang:<3} {b.name}")
            else:
                verify_ok = False
                log(f"  FAIL {lang:<3} {b.name} (got {len(got)}B want {len(want)}B)")
    log("")

    if args.verify_only:
        text = "\n".join(lines) + "\n"
        if args.out:
            Path(args.out).write_text(text)
        raise SystemExit(0 if verify_ok else 1)

    # Full-size content gate. Keep this before every timed run: each available
    # binary executes once, stdout is streamed through SHA-256, and only then
    # may performance sampling begin.
    log("## verify (perf-N stdout fingerprint; untimed)")
    full_verify_ok = True
    for b in selected:
        full_verify_ok &= verify_full_stdout(
            b, bins, perf_n_for(b, args.quick), log
        )
    log("")
    verify_ok = verify_ok and full_verify_ok
    if not verify_ok:
        log("# output verification failed; timing skipped")
        text = "\n".join(lines) + "\n"
        if args.out:
            Path(args.out).write_text(text)
        raise SystemExit(1)

    # perf
    log(
        f"## perf wall (median/best of {args.iters}, ms; cell = med (best))"
    )
    hdr = f"{'bench':<16} {'xu':>14} {'c':>14} {'c++':>14} {'rust':>14} {'go':>14}"
    log(hdr)
    # label -> {best, med, rss_mib, cpu_ms}
    results: dict[str, dict[str, dict[str, float]]] = {}
    curves_by_bench: dict[str, dict[str, tuple]] = {}
    for b in selected:
        perf_n = perf_n_for(b, args.quick)
        if b.name == "fannkuchredux" and not args.quick:
            print(
                "fannkuchredux N=12 is ~2 min per Xu run; "
                "5 langs x --iters with no row until all finish",
                file=sys.stderr,
                flush=True,
            )
        row: dict[str, dict[str, float]] = {}
        cells = []
        for lang, label in (
            ("xu", "xu"),
            ("c", "c"),
            ("cc", "c++"),
            ("rs", "rust"),
            ("go", "go"),
        ):
            key = (lang, b.name)
            if key not in bins:
                cells.append(f"{'—':>14}")
                continue
            print(
                f"timing {b.name} {label} N={perf_n} ({args.iters}x)",
                file=sys.stderr,
                flush=True,
            )
            st = timed_perf(
                bins[key],
                perf_n,
                b.binary,
                args.iters,
                args.discard_first,
                sample_interval_s=sample_s,
            )
            best_ms = st.best_s * 1000
            med_ms = st.med_s * 1000
            row[label] = {
                "best": best_ms,
                "med": med_ms,
                "rss_mib": st.med_rss_mib,
                "cpu_ms": st.med_cpu_s * 1000,
            }
            if st.rss_curve:
                curves_by_bench.setdefault(b.name, {})[label] = st.rss_curve
            cells.append(f"{med_ms:6.1f} ({best_ms:5.1f})")
        results[b.name] = row
        log(f"{b.name:<16} " + " ".join(cells) + f"   N={perf_n}")

    log("")
    log(f"## peak RSS MiB (median of {args.iters})")
    log(hdr)
    for b in selected:
        row = results.get(b.name, {})
        cells = []
        for label in ("xu", "c", "c++", "rust", "go"):
            if label not in row:
                cells.append(f"{'—':>14}")
            else:
                cells.append(f"{row[label]['rss_mib']:14.2f}")
        log(f"{b.name:<16} " + " ".join(cells))

    log("")
    log(f"## CPU user+sys ms (median of {args.iters})")
    log(hdr)
    for b in selected:
        row = results.get(b.name, {})
        cells = []
        for label in ("xu", "c", "c++", "rust", "go"):
            if label not in row:
                cells.append(f"{'—':>14}")
            else:
                cells.append(f"{row[label]['cpu_ms']:14.1f}")
        log(f"{b.name:<16} " + " ".join(cells))

    log("")
    log("## Xu / other (ratio on median; >1 means Xu higher)")
    for b in selected:
        row = results.get(b.name, {})
        xu = row.get("xu")
        if xu is None:
            continue
        bits = [f"### {b.name}  ({b.face})"]
        for label in ("c", "c++", "rust", "go"):
            if label in row and row[label]["med"] > 0:
                o = row[label]
                bits.append(
                    f"  vs {label}: wall {xu['med'] / o['med']:.2f}×  "
                    f"rss {xu['rss_mib'] / o['rss_mib']:.2f}×  "
                    f"cpu {xu['cpu_ms'] / o['cpu_ms']:.2f}×  "
                    f"(wall med {xu['med']:.1f}/{o['med']:.1f}; "
                    f"rss {xu['rss_mib']:.2f}/{o['rss_mib']:.2f} MiB)"
                )
        log("\n".join(bits))
        log("")

    curves_dir: Path | None = None
    if sample_s is not None and curves_by_bench:
        if args.curves_dir:
            curves_dir = Path(args.curves_dir)
        elif args.out:
            curves_dir = Path(str(Path(args.out)) + ".curves")
        else:
            curves_dir = tmp / "curves"
        curves_dir.mkdir(parents=True, exist_ok=True)
        log("## RSS curves")
        for bench_name, series in curves_by_bench.items():
            for label, curve in series.items():
                write_curve_csv(curves_dir / f"{bench_name}__{label}.csv", curve)
            svg = curves_dir / f"{bench_name}.svg"
            write_rss_svg(svg, series, title=f"{bench_name} RSS over time")
            log(f"  {svg}  ({len(series)} series)")
            for label, curve in series.items():
                log(
                    f"    {label:<8} n={len(curve):4d}  "
                    f"peak={max(r for _t, r in curve):.2f} MiB  "
                    f"{sparkline(curve)}"
                )
        log(f"# curves dir: {curves_dir}")

    text = "\n".join(lines) + "\n"
    if args.out:
        Path(args.out).write_text(text)
        log(f"# wrote {args.out}")
    log(f"# bins in {tmp}")

    if args.report:
        write_report(Path(args.report), host, selected, results, verify_ok, args)
        log(f"# wrote {args.report}")

    raise SystemExit(0 if verify_ok else 1)


def write_report(
    path: Path,
    host: str,
    selected: list[Bench],
    results: dict[str, dict[str, dict[str, float]]],
    verify_ok: bool,
    args,
):
    lines = [
        "# BENCH_GAME_REPORT — Benchmarks Game 横向对照",
        "",
        f"**日期**: {time.strftime('%Y-%m-%d')}  ",
        f"**主机**: `{host}`  ",
        "**对照**: Xu / C (`clang -O3`) / C++ (`clang++|g++ -O3`) / Rust (`rustc -C opt-level=3`) / Go (`go build`)  ",
        "**规则**: 单线程、同算法直译、禁手写 SIMD；小 N 对齐官方 golden，"
        "计时 N 在采样前以流式 SHA-256+长度跨实现对齐。  ",
        f"**计时**: median（主）+ best wall；median peak RSS + CPU；"
        f"`--discard-first={args.discard_first}`；iters={args.iters}。  ",
        f"**verify**: {'小 N golden 与计时 N 指纹全绿' if verify_ok else '有失败'}  ",
        "",
        "## 摘要",
        "",
        "Wave 1 六题玩具负载上的相对水位（Xu / 对照；>1 表示 Xu 更高；比值用 median）。"
        " 详细见下表与 `bench_game.latest.txt`。",
        "",
        "## 结果表（wall ms；median，括号内 best）",
        "",
        "| bench | Xu | C | C++ | Rust | Go | Xu/C | Xu/C++ | Xu/Rust | Xu/Go |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for b in selected:
        row = results.get(b.name, {})
        xu = row.get("xu")

        def cell(k):
            v = row.get(k)
            if v is None:
                return "—"
            return f"{v['med']:.1f} ({v['best']:.1f})"

        def ratio(k):
            if xu is None or k not in row or row[k]["med"] <= 0:
                return "—"
            return f"{xu['med'] / row[k]['med']:.2f}×"

        lines.append(
            f"| {b.name} | {cell('xu')} | {cell('c')} | {cell('c++')} | {cell('rust')} | {cell('go')} "
            f"| {ratio('c')} | {ratio('c++')} | {ratio('rust')} | {ratio('go')} |"
        )
    lines += [
        "",
        "## 峰值 RSS（MiB，median）",
        "",
        "| bench | Xu | C | C++ | Rust | Go | Xu/C | Xu/C++ | Xu/Rust | Xu/Go |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for b in selected:
        row = results.get(b.name, {})
        xu = row.get("xu")

        def rcell(k):
            v = row.get(k)
            return f"{v['rss_mib']:.2f}" if v is not None else "—"

        def rratio(k):
            if xu is None or k not in row or row[k]["rss_mib"] <= 0:
                return "—"
            return f"{xu['rss_mib'] / row[k]['rss_mib']:.2f}×"

        lines.append(
            f"| {b.name} | {rcell('xu')} | {rcell('c')} | {rcell('c++')} | {rcell('rust')} | {rcell('go')} "
            f"| {rratio('c')} | {rratio('c++')} | {rratio('rust')} | {rratio('go')} |"
        )
    lines += [
        "",
        "## 分题读数",
        "",
    ]
    notes = {
        "nbody": "f64 多体积分 + 结构体字段；看浮点与小数组热圈。",
        "fannkuchredux": "整数置换与翻面；看整数 ALU / 分支。",
        "spectralnorm": "稠密 f64 矩阵式幂迭代；看嵌套循环浮点。",
        "mandelbrot": "复数迭代 + 位打包 PBM；看 f64 与字节写出。",
        "fasta": "经典 LCG 与加权选碱基；看整数 RNG 与大量 stdout。",
        "binarytrees": "完全二叉树分配；Xu 用节点池（非 GC），对照为堆指针树。",
    }
    for b in selected:
        row = results.get(b.name, {})
        xu = row.get("xu")
        lines.append(f"### {b.name}")
        lines.append("")
        lines.append(notes.get(b.name, b.face))
        if xu is not None:
            parts = []
            for k in ("c", "c++", "rust", "go"):
                if k in row and row[k]["med"] > 0:
                    o = row[k]
                    parts.append(
                        f"相对 {k} wall **{xu['med'] / o['med']:.2f}×** / "
                        f"rss **{xu['rss_mib'] / o['rss_mib']:.2f}×**"
                    )
            if parts:
                lines.append("Xu " + "，".join(parts) + "（median）。")
        lines.append("")
    lines += [
        "## 与能力套件关系",
        "",
        "语言能力微基准见 `tests/bench/` 与 `docs/audit/BENCH_RUNTIME.md`。",
        "本套件对齐 [Benchmarks Game](https://benchmarksgame-team.pages.debian.net/benchmarksgame/) 题意，不混进 `bench_crosslang.py`。",
        "",
        "## 限制",
        "",
        "- 玩具程序，不定义「哪种语言最快」。",
        "- 单线程；非 BG 多线程冲榜写法。",
        "- Wave 2（revcomp / knucleotide / pidigits / regexredux）未测。",
        "- RSS 为进程生命周期峰值（`wait4` `ru_maxrss`）+ 运行中采样曲线（CSV/SVG）。",
        "- 不入 CI；安静机器人工取证。",
        "",
    ]
    path.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
