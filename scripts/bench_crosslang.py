#!/usr/bin/env python3
"""Language-capability efficiency suite: Xu vs Go / C / Rust / Swift.

Same algorithm, same integer width (i64), while-counted loops, locked stdout.
Not SPECcpu. Ports live in tests/bench/cross/; Xu sources in tests/bench/*.xu.

Method (plb2-style): whole-program wall time; same algorithm (not peak golf);
report best + median wall, median peak RSS + CPU (user+sys); ratios use median.
Also report on-disk binary size (not stripped) with Xu/peer ratios.
Optional --discard-first drops cold run.

Usage:
  python3 scripts/bench_crosslang.py --out /tmp/xu_cross.txt
  python3 scripts/bench_crosslang.py --out /tmp/xu_cross.txt --benches=loop_sum,fib
  python3 scripts/bench_crosslang.py --out /tmp/xu_cross.txt --discard-first
  python3 scripts/bench_crosslang.py --list
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

if sys.platform == "win32":
    # Rewrapping an existing buffer gives two streams ownership of the same
    # descriptor and closes pytest's capture buffer when either is collected.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench_rusage import (  # noqa: E402
    peak_rss_method,
    run_one,
    sparkline,
    write_curve_csv,
    write_rss_svg,
)
from bench_network import wait_for_loopback_capacity

BENCH_ROOT = Path(__file__).resolve().parents[1]
xu_env = os.environ.get("XU_ROOT")
if xu_env and (Path(xu_env) / "scripts").is_dir():
    ROOT = Path(xu_env).expanduser().resolve()
elif (BENCH_ROOT.parent / "xu").is_dir():
    ROOT = (BENCH_ROOT.parent / "xu").resolve()
else:
    ROOT = Path(xu_env or BENCH_ROOT.parent / "xu").expanduser().resolve()
os.environ["XU_ROOT"] = str(ROOT)

sys.path.insert(0, str(ROOT / "scripts"))
from product_compiler import resolve_product_compiler as resolve_hosted_compiler, product_compile_argv
CROSS = BENCH_ROOT / "tests" / "bench" / "cross"
PRODUCT_XU = ROOT / "bin" / "xu"
HOST_SEED_RESOLVER = ROOT / "scripts" / "xu_host_seed.sh"
PRODUCT_RUNNER = ROOT / "scripts" / "run_product_compiler.sh"
# Keep the canonical names visible to the boundary checker and to downstream
# benchmark tooling; both names intentionally point at the same wrapper.
PRODUCT_COMPILER_RUNNER = PRODUCT_RUNNER

LANE = "product"

RUN_ITERS = 7
COMPILE_ITERS = 5

# The cross-language comparison is deliberately profile-complete for the
# native AOT compilers.  An optimisation result is meaningful only when the
# corresponding Xu, Clang and rustc levels are present in the same report.
XU_LEVELS = (
    (1, "Xu", [], "prod"),
)
C_LEVELS = (
    (1, "clang -O1", ["-O1"], "o1"),
    (2, "clang -O2", ["-O2"], "o2"),
    (3, "clang -O3", ["-O3"], "o3"),
)
RUST_LEVELS = (
    (1, "rustc -O1", ["-C", "opt-level=1"], "o1"),
    (2, "rustc -O2", ["-C", "opt-level=2"], "o2"),
    (3, "rustc -O3", ["-C", "opt-level=3"], "o3"),
)
XU_BASE = "Xu"


def c_profiles(compiler: str) -> tuple:
    """Keep C optimization levels comparable without relabelling GCC as Clang."""
    return tuple((level, f"{compiler} -O{level}", list(flags), tag)
                 for level, _label, flags, tag in C_LEVELS)


def select_c_compiler(explicit: str | None, target: str | None) -> str:
    # Apple cross-target flags require Clang; host builds may use GCC.
    name = explicit or ("clang" if target or which("clang") else "gcc")
    if target and name != "clang":
        raise SystemExit("--xu-target requires --cc=clang")
    if explicit and not which(name):
        raise SystemExit(f"requested C compiler unavailable: {name}")
    return name


def median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        raise ValueError("empty samples")
    mid = n // 2
    if n % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


def resolve_product_compiler(explicit: str | None) -> Path:
    return resolve_hosted_compiler(explicit)


# Stable seam name shared with the other product benchmark drivers.
resolve_product_xu = resolve_product_compiler


@dataclass(frozen=True)
class RunStats:
    best_s: float
    med_s: float
    med_rss_mib: float
    max_rss_mib: float
    med_cpu_s: float
    stdout: str
    # curve from the sample whose wall is closest to median
    rss_curve: tuple[tuple[float, float], ...] = ()


@dataclass(frozen=True)
class Bench:
    name: str
    expect: str
    face: str
    langs: tuple[str, ...]
    xu_opt_matrix: bool = False
    loopback_connections: int = 0


CORE = ("go", "c", "rs", "swift")
APPLE_CRYPTO = CORE if sys.platform == "darwin" else ("go", "c", "rs")

BENCHES: list[Bench] = [
    Bench("startup", "", "进程启动/空 main", CORE),
    Bench("loop_sum", "25574942656\n", "整数循环", CORE, xu_opt_matrix=True),
    Bench("fib", "5702887\n", "递归调用", CORE, xu_opt_matrix=True),
    Bench("nested_loop", "32572980224\n", "嵌套循环", CORE),
    Bench("method_sum", "28000000\n", "结构体方法", CORE),
    Bench("f64_sum", "10229901696\n", "f64 算术", CORE),
    Bench("matmul", "4092083497262\n", "嵌套循环+数组下标(i64 matmul)", CORE),
    Bench("string_build", "52500000\n1000000\n", "字符串增长/扫描", CORE),
    Bench("string_repeat", "473812500\n", "字符串重复(独立结果与倍增复制)", CORE),
    Bench("array_ops", "7000000\n", "数组增长/索引", CORE),
    Bench("file_roundtrip", "6240\n", "文件写入+读取（32 × 512KiB）", CORE),
    Bench("sort_lcg", "8588477465\n", "stdlib 排序", CORE),
    Bench(
        "algorithm_search",
        "393215066828\n",
        "stdlib 二分查找",
        CORE,
        xu_opt_matrix=True,
    ),
    Bench(
        "math_bits",
        "-8160978732932967136\n",
        "stdlib 位运算（硬件指令）",
        CORE,
        xu_opt_matrix=True,
    ),
    Bench("sha256_chain", "131ea75bef251e81744c71ecb216e3d799e00c26c52677d19c9d026d6b6fa5aa\n", "哈希计算", APPLE_CRYPTO),
    Bench(
        "chan_ping",
        "124999750000\n",
        "channel/调度",
        ("go", "rs"),
    ),
    Bench(
        "http_concurrent",
        "3200\n35945209188\n",
        "HTTP 高并发吞吐(自环回,16 并发 x 200 请求)",
        ("go", "rs"),
        loopback_connections=3200,
    ),
    Bench("map_ops", "20000100000\n", "哈希表插入/查找", CORE),
    Bench("iface_sum", "20000000\n", "接口动态派发", CORE),
    Bench("match_sum", "228000000\n24000000\n", "密集 match/switch", CORE, xu_opt_matrix=True),
    Bench("fn_val_sum", "36000000\n", "函数值间接调用", CORE),
    Bench("copy_bytes", "536346624\n", "块拷贝 LoadIndex/StoreIndex", CORE),
    Bench("sroa_vec3", "537600000\n", "AoS f64 字段归约", CORE),
    Bench("scan_dep", "2378880\n", "进位依赖链 prefix-add", CORE),
    Bench("chase_index", "54272\n", "数据相关下标追逐", CORE),
    Bench("sieve_primes", "148933\n142913828922\n", "埃氏素数筛法(连续内存写入)", CORE),
    Bench("crc32_iso", "38153323000\n", "CRC32 数据流校验和吞吐", CORE),
    Bench("builder", "5250000\n100000\n", "字符串构建器(动态扩容与视图遍历)", CORE),
    Bench("byte_view", "40\n100000\n", "字符串切片视图(子串与字节搜索)", CORE),
    Bench("strings_io", "188165000\n", "字符串综合处理(repeat/split/join/cursor)", CORE),
    Bench("string_count", "5844359\n", "短串字节计数(动态输入/目标,100万次)", CORE),
    Bench("heap_priority", "144699053\n", "二叉堆优先队列(30万次下沉上浮)", CORE),
    Bench("hex_codec", "42600164\n", "十六进制编解码(2.5万次查表流)", CORE),
    Bench("base64_codec", "14910164\n", "Base64编解码(1.5万次协议流)", CORE),
    Bench("ring_buffer", "855584727\n", "双端环形缓冲区(500万次动态扩容)", CORE),
    Bench("md5_chain", "f0bab2b4771e3638b3c031a6e0a5ca52\n", "MD5链式消息摘要(10万轮散列)", APPLE_CRYPTO),
    Bench("quicksort_hoare", "895282358\n", "Hoare双指针快速排序(50万元素递归分区)", CORE),
    Bench("lru_cache", "455153392\n", "LRU缓存机制(250万次Get/Put与链表淘汰)", CORE),
    Bench("bloom_filter", "175597838\n", "布隆过滤器(100万位位图与200万次查验)", CORE),
    Bench('aes128_encrypt', '8a2a156f9b87fd7576be4a13c3e41c5d\n', 'AES软件 128 encrypt', CORE, xu_opt_matrix=True),
    Bench('aes128_decrypt', '11f9740af24d70e78f50b5b407664176\n', 'AES软件 128 decrypt', CORE, xu_opt_matrix=True),
    Bench('aes128_key_setup', '1087987\n', 'AES软件 128 key_setup', CORE, xu_opt_matrix=True),
    Bench('aes192_encrypt', '027a490ebdb3ccf2dd1057d638e293c2\n', 'AES软件 192 encrypt', CORE, xu_opt_matrix=True),
    Bench('aes192_decrypt', '6ed8119f2abe0dc846d74d24cc426801\n', 'AES软件 192 decrypt', CORE, xu_opt_matrix=True),
    Bench('aes192_key_setup', '1319771\n', 'AES软件 192 key_setup', CORE, xu_opt_matrix=True),
    Bench('aes256_encrypt', '05e02782a54c19f76b3397c6e5855a6c\n', 'AES软件 256 encrypt', CORE, xu_opt_matrix=True),
    Bench('aes256_decrypt', '4b1a2e40a8a6ad8761b3a6fca8719ee5\n', 'AES软件 256 decrypt', CORE, xu_opt_matrix=True),
    Bench('aes256_key_setup', '1033425\n', 'AES软件 256 key_setup', CORE, xu_opt_matrix=True),
    # Osprey original algorithms/workloads (MIT); tests/bench/osprey/README.md.
    Bench('ackermann', '8189\n', 'Osprey: Ackermann-Peter function ack(3,10) — deep non-tail recursion', CORE),
    Bench('osprey_binarytrees', '19659600\n', 'Osprey: 1200 owning binary trees of depth 13; build then check (16383 nodes each)', CORE),
    Bench('coins', '116727\n', 'Osprey: Count ways to make 600 from coins [1,5,10,25,50] — combinatorial recursion (SICP)', CORE),
    Bench('collatz', '10753840\n', 'Osprey: Sum of Collatz (3n+1) stopping times over 1..100000 — integer division n/2 in deep recursion', CORE),
    Bench('osprey_coprime', '2433175\n', 'Osprey: Count coprime pairs in a 2000x2000 grid — nested iteration + Euclidean gcd', CORE),
    Bench('digitsum', '55000002\n', 'Osprey: Sum of decimal digit-sums over 1..2000000 — integer division n/10 and modulo', CORE),
    Bench('expr_tree', '900720437\n', 'Osprey: 10 owning expression trees of depth 14; build then modular-evaluate', CORE),
    Bench('factorial_mod', '682498929\n', 'Osprey: Product 1..10,000,000 mod 1000000007 — multiplication-heavy fold', CORE),
    Bench('osprey_fib', '9227465\n', 'Osprey: Naive recursive Fibonacci, fib(35) — function-call & recursion overhead', CORE),
    Bench('gcd_sum', '7201567\n', 'Osprey: Sum of gcd(i,1234567) for i in 1..1999999 — Euclidean recursion, modulo heavy', CORE),
    Bench('hanoi', '33554431\n', 'Osprey: Towers of Hanoi move count (n=25) — exponential double recursion', CORE),
    Bench('isqrt', '666167500\n', "Osprey: Sum of integer square roots over 1..1000000 — Newton's method, integer division heavy", CORE),
    Bench('josephus', '1400177\n', 'Osprey: Josephus survivor index (n=10,000,000, k=7) — modular iteration', CORE),
    Bench('osprey_listops', '15992435\n', 'Osprey: 8 growable vectors x 4000 integers; recursive sum and count-below traversals', CORE),
    Bench('merge_sort', '563434287\n', 'Osprey: 8 x 2000 values; alternating split, recursive merge sort with fresh vectors; rank checksum', CORE),
    Bench('mutual_recursion', '64999\n', 'Osprey: Mutually recursive parity of i%1000, 1 <= i < 130000', CORE),
    Bench('osprey_nestedloop', '255643180\n', 'Osprey: Triple-nested loop 250^3 accumulating (i*j*k) mod 1000000007 — nested iteration', CORE),
    Bench('pascal', '20058300\n', 'Osprey: Binomial C(27,13) via naive un-memoised Pascal recursion — exponential recursion', CORE),
    Bench('powmod', '980475159\n', 'Osprey: Sum i^20 mod 1000000007, 1 <= i < 1000000; twenty modular multiplies', CORE),
    Bench('osprey_primes', '17984\n', 'Osprey: Count primes below 200000 by trial division — integer modulo in a hot loop', CORE),
    Bench('osprey_quicksort', '563434287\n', 'Osprey: 8 x 2000 values; first-element pivot, two partition passes, fresh vectors; rank checksum', CORE),
    Bench('tak', '9\n', 'Osprey: Takeuchi function tak(32,16,8) — heavy ternary self-recursion', CORE),
    Bench('osprey_textstats', '1574956\n', 'Osprey: 200000 tokens, 8 words; length + contains(o) + startsWith(t)', CORE),
    Bench('word_frequency', '900036\n', 'Osprey: 200000 tokens, 8 words; string-keyed frequency map, weighted counts', CORE),
]

BY_NAME = {b.name: b for b in BENCHES}


class _CmdResult:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def run(cmd, **kw):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, **kw)
    except Exception as e:
        return _CmdResult(stdout="", stderr=str(e), returncode=1)


def timed_runs(
    path: str,
    n: int,
    discard_first: bool = False,
    sample_interval_s: float | None = None,
    timeout_s: float | None = None,
    cwd: Path | None = None,
    before_run=None,
) -> RunStats:
    """Wall best/median + median peak RSS + median CPU.

    Timing runs never sample (keeps wall clean). If sample_interval_s is set,
    one extra run captures the RSS curve.
    """
    walls: list[float] = []
    rss: list[float] = []
    cpus: list[float] = []
    out = ""
    total = n + (1 if discard_first else 0)
    for i in range(total):
        if before_run is not None:
            before_run()
        s = run_one(
            [path], sample_interval_s=None, timeout_s=timeout_s, cwd=cwd, verify_rss_output=True
        )
        if timeout_s is not None and s.wall_s >= timeout_s and s.returncode != 0:
            raise SystemExit(f"TIMEOUT {path}: {s.wall_s:.1f}s >= {timeout_s:.1f}s")
        if s.returncode != 0:
            err = s.stderr.decode("utf-8", "replace")[-400:]
            raise SystemExit(f"run failed {path}: {err}")
        text = s.stdout.decode("utf-8", "replace")
        if discard_first and i == 0:
            continue
        walls.append(s.wall_s)
        rss.append(s.max_rss_mib)
        cpus.append(s.cpu_s)
        out = text
    curve: tuple[tuple[float, float], ...] = ()
    if sample_interval_s is not None and sample_interval_s > 0:
        if before_run is not None:
            before_run()
        cs = run_one(
            [path],
            sample_interval_s=sample_interval_s,
            verify_rss_output=True,
            timeout_s=timeout_s,
            cwd=cwd,
        )
        if cs.returncode != 0:
            err = cs.stderr.decode("utf-8", "replace")[-400:]
            raise SystemExit(f"curve run failed {path}: {err}")
        curve = cs.rss_curve
        # prefer curve-run stdout only if timing had none (shouldn't happen)
        if not out:
            out = cs.stdout.decode("utf-8", "replace")
    return RunStats(
        best_s=min(walls),
        med_s=median(walls),
        med_rss_mib=median(rss),
        max_rss_mib=max(rss),
        med_cpu_s=median(cpus),
        stdout=out,
        rss_curve=curve,
    )


def _curve_slug(name: str) -> str:
    return (
        name.replace(" ", "_")
        .replace("-", "")
        .replace("/", "_")
        .replace(".", "p")
    )


def best_compile(cmd: list[str], n: int) -> float:
    times: list[float] = []
    for _ in range(n):
        t0 = time.perf_counter()
        p = run(cmd)
        dt = time.perf_counter() - t0
        if p.returncode != 0:
            raise SystemExit(
                f"compile failed {cmd}:\n{p.stderr[-800:] or p.stdout[-400:]}"
            )
        times.append(dt)
    return min(times)


def which(name: str) -> str | None:
    return shutil.which(name)


def ver_line(cmd: list[str]) -> str:
    p = run(cmd)
    s = (p.stdout or p.stderr).strip().splitlines()
    return s[0] if s else "?"


def xu_src(name: str) -> Path:
    return BENCH_ROOT / "tests" / "bench" / f"{name}.xu"


def cross_src(name: str, ext: str) -> Path:
    return CROSS / f"{name}.{ext}"


def peer_sources(name: str, ext: str) -> list[str]:
    sources = [str(cross_src(name, ext))]
    # C includes the header and Rust resolves `mod aes_software`; Go and
    # Swift need the shared software kernel passed as another source file.
    if name.startswith(("aes128_", "aes192_", "aes256_")) and ext in ("go", "swift"):
        sources.append(str(CROSS / f"aes_software.{ext}"))
    return sources


def parse_benches(s: str | None) -> list[Bench]:
    if not s:
        return list(BENCHES)
    out = []
    for part in s.split(","):
        name = part.strip()
        if not name:
            continue
        if name not in BY_NAME:
            raise SystemExit(
                f"unknown bench {name!r}; known: {', '.join(BY_NAME)}"
            )
        out.append(BY_NAME[name])
    if not out:
        raise SystemExit("empty --benches")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="write report here (required unless --list)")
    ap.add_argument(
        "--xu",
        default=os.environ.get("XU_COMPILER"),
        help="hosted product Xu compiler (default: canonical hosted seed resolver)",
    )
    ap.add_argument(
        "--xu-target",
        choices=("macos-arm64", "macos-x64"),
        help="benchmark a macOS target emitted by product Xu (x64 uses Rosetta)",
    )
    ap.add_argument("--cc", choices=("clang", "gcc"),
                    help="C compiler (default: clang, falling back to gcc on the host)")
    ap.add_argument("--skip-compile-times", action="store_true")
    ap.add_argument(
        "--benches",
        help="comma-separated subset, e.g. loop_sum,fib",
    )
    ap.add_argument(
        "--quick",
        action="store_true",
        help="skip debug-peer builds and compile-time section; keep Xu/C/Rust O1–O3",
    )
    ap.add_argument(
        "--full",
        action="store_true",
        help="debug language builds for every bench (O1–O3 are always included)",
    )
    ap.add_argument(
        "--iters",
        type=int,
        default=RUN_ITERS,
        help=f"timed runs per binary (default {RUN_ITERS})",
    )
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
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    if args.out:
        Path(args.out).expanduser().parent.mkdir(parents=True, exist_ok=True)
    if args.iters < 1:
        raise SystemExit("--iters must be >= 1")
    if args.sample_ms < 0:
        raise SystemExit("--sample-ms must be >= 0")

    if args.list:
        print(f"{'bench':<16} {'langs':<22} face")
        for b in BENCHES:
            print(f"{b.name:<16} {','.join(b.langs):<22} {b.face}")
        return

    if not args.out:
        raise SystemExit("--out is required (or use --list)")

    xu_compiler = resolve_product_xu(args.xu)

    selected = parse_benches(args.benches)
    import platform
    raw_machine = platform.machine().lower()
    if raw_machine in ("arm64", "aarch64"):
        host_machine = "arm64"
    elif raw_machine in ("x86_64", "amd64"):
        host_machine = "x86_64"
    else:
        host_machine = raw_machine

    if args.xu_target == "macos-arm64" and host_machine != "arm64":
        raise SystemExit("macos-arm64 benchmark execution requires an arm64 host")
    if args.xu_target == "macos-x64" and host_machine not in ("arm64", "x86_64"):
        raise SystemExit("macos-x64 benchmark execution requires x64 or Rosetta")
    cross_arch = args.xu_target == "macos-x64" and host_machine == "arm64"
    if cross_arch:
        unsupported = [b.name for b in selected if "c" not in b.langs]
        if unsupported:
            raise SystemExit(
                "cross-architecture comparison requires a C peer; "
                f"unsupported: {', '.join(unsupported)}"
            )
    xu_target_flags = (
        ["--target", args.xu_target] if args.xu_target else []
    )
    clang_arch_flags: list[str] = []
    if sys.platform == "darwin" and Path("/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk").exists():
        clang_arch_flags.extend(["-isysroot", "/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk"])
    if args.xu_target == "macos-arm64":
        clang_arch_flags.extend(["-arch", "arm64"])
    elif args.xu_target == "macos-x64":
        clang_arch_flags.extend(["-arch", "x86_64"])
    want_debug_peers = args.full or not args.quick
    tmp = Path(tempfile.mkdtemp(prefix="xu_cross_"))
    # Swift's default module cache may live outside the writable workspace.
    # Use a suite-local cache for both runtime builds and compile-time samples.
    swift_cache_flags = ["-module-cache-path", str(tmp / "swift-module-cache")]
    lines: list[str] = []

    def log(s=""):
        print(s, flush=True)
        lines.append(s)

    host = f"{platform.system()} {platform.machine()}"
    log(f"# host: {host}")
    log(f"# date: {time.strftime('%Y-%m-%d %H:%M')}")
    log(f"# lane: {LANE}")
    log(f"# xu: {xu_compiler} (hosted product)")
    log(f"# xu target: {args.xu_target or 'host default'}")
    disc = " discard-first=yes" if args.discard_first else " discard-first=no"
    sample_s = None if args.sample_ms <= 0 else args.sample_ms / 1000.0
    curves_dir: Path | None = None
    if sample_s is not None:
        if args.curves_dir:
            curves_dir = Path(args.curves_dir)
        else:
            curves_dir = Path(str(Path(args.out)) + ".curves")
    log(
        f"# run: best+median wall of {args.iters}{disc}; "
        f"median peak RSS + CPU(user+sys); compile best-of-{COMPILE_ITERS}; "
        "time ratios use median wall"
    )
    if sample_s is None:
        log("# curves: disabled (--sample-ms=0)")
    else:
        log(
            f"# curves: live RSS every {args.sample_ms:g}ms -> {curves_dir}"
        )
    log(
        "# method: plb2-style whole-program wall; same algorithm (not peak golf); "
        "AOT no warmup; startup is an intentional short-process cell; "
        "RSS collected separately on Linux; curve=live poll (libproc|/proc|ps)"
    )
    log(f"# rss_method: {peak_rss_method()}")
    log(
        "# suite: language-capability (same algorithm; int=i64; while-counted)"
    )
    log(f"# benches: {', '.join(b.name for b in selected)}")
    if cross_arch:
        log("# cross-arch peers: clang only (Go/Rust/Swift host binaries omitted)")
    # Cross-target Apple flags require Clang. GCC fallback is host-only and
    # must retain its own identity in every timing/size/compile row.
    c_name = select_c_compiler(args.cc, args.xu_target)
    c_levels = c_profiles(c_name)
    tools = {
        "go": which("go"),
        "cc": which(c_name),
        "rustc": which("rustc"),
        "swiftc": which("swiftc"),
    }
    if tools["go"]:
        log(f"# go: {ver_line(['go', 'version'])}")
    if tools["cc"]:
        log(f"# {c_name}: {ver_line([c_name, '--version'])}")
    if tools["rustc"]:
        log(f"# rustc: {ver_line(['rustc', '--version'])}")
    if tools["swiftc"]:
        log(f"# swiftc: {ver_line(['swiftc', '--version'])}")
    log("")

    jobs: list[tuple[str, str, list[str], Path]] = []
    ext = ".exe" if sys.platform == "win32" else ""

    def add(name, bench, cmd, out_bin):
        jobs.append((name, bench, cmd, out_bin))

    def xu_compile_argv(src: Path, flags: list[str], out: Path) -> list[str]:
        return product_compile_argv(xu_compiler, "build", str(src),
                                    *xu_target_flags, *flags, "-o", str(out),
                                    runner=PRODUCT_RUNNER)

    def add_xu(bench: Bench, flags: list[str], label: str, tag: str):
        out = tmp / f"xu_{bench.name}_{tag}{ext}"
        add(label, bench.name, xu_compile_argv(xu_src(bench.name), flags, out), out)

    for bench in selected:
        add_xu(bench, [], "Xu", "prod")
        if want_debug_peers and bench.xu_opt_matrix:
            add_xu(bench, ["--no-opt"], "xu --no-opt", "noopt")

        langs = bench.langs
        if "go" in langs and tools["go"] and not cross_arch:
            out = tmp / f"go_{bench.name}{ext}"
            add(
                "go build",
                bench.name,
                ["go", "build", "-o", str(out), *peer_sources(bench.name, "go")],
                out,
            )
        if "c" in langs and tools["cc"]:
            src = cross_src(bench.name, "c")
            if args.full or (want_debug_peers and bench.xu_opt_matrix):
                out0 = tmp / f"c_{bench.name}_o0{ext}"
                add(
                    f"{c_name} -O0",
                    bench.name,
                    [c_name, *clang_arch_flags, "-O0", "-o", str(out0), str(src)],
                    out0,
                )
            for _level, label, flags, tag in c_levels:
                out = tmp / f"c_{bench.name}_{tag}{ext}"
                add(
                    label,
                    bench.name,
                    [c_name, *clang_arch_flags, *flags, "-o", str(out), str(src)],
                    out,
                )
        if "rs" in langs and tools["rustc"] and not cross_arch:
            src = cross_src(bench.name, "rs")
            if args.full or (want_debug_peers and bench.xu_opt_matrix):
                out0 = tmp / f"rs_{bench.name}_o0{ext}"
                add(
                    "rustc -O0",
                    bench.name,
                    ["rustc", "-C", "opt-level=0", "-o", str(out0), str(src)],
                    out0,
                )
            for _level, label, flags, tag in RUST_LEVELS:
                out = tmp / f"rs_{bench.name}_{tag}{ext}"
                add(
                    label,
                    bench.name,
                    ["rustc", *flags, "-o", str(out), str(src)],
                    out,
                )
        if "swift" in langs and tools["swiftc"] and not cross_arch:
            src = cross_src(bench.name, "swift")
            if args.full or (want_debug_peers and bench.xu_opt_matrix):
                out0 = tmp / f"sw_{bench.name}_none{ext}"
                add(
                    "swiftc -Onone",
                    bench.name,
                    ["swiftc", *swift_cache_flags, "-Onone", "-o", str(out0), *peer_sources(bench.name, "swift")],
                    out0,
                )
            outo = tmp / f"sw_{bench.name}_o{ext}"
            add("swiftc -O", bench.name, ["swiftc", *swift_cache_flags, "-O", "-o", str(outo), *peer_sources(bench.name, "swift")], outo)

    log("## runtime + resources + binary size")
    log(
        f"{'impl':<22} {'bench':<14} {'best_ms':>8} {'med_ms':>8} "
        f"{'rss_mib':>8} {'cpu_ms':>8} {'bytes':>10}  stdout"
    )
    # (impl, bench, best_ms, med_ms, rss_mib, cpu_ms, bytes, ok, curve)
    results: list[
        tuple[str, str, float, float, float, float, int, str, tuple]
    ] = []
    # bench -> {impl: curve}
    curves_by_bench: dict[str, dict[str, tuple]] = {}
    # Every executable runs in a private benchmark directory. This keeps file
    # I/O payloads out of the checkout and gives every language the same path.
    run_dirs: dict[str, Path] = {}
    for bench in selected:
        run_dir = tmp / "run" / bench.name
        run_dir.mkdir(parents=True, exist_ok=True)
        run_dirs[bench.name] = run_dir
    fail_mismatch = False
    xu_base_s: dict[str, float] = {}
    for name, bench, cmd, out_bin in jobs:
        p = run(cmd)
        if p.returncode != 0:
            fail_mismatch = True
            log(
                f"{name:<22} {bench:<14} {'FAIL':>8} {'':>8} "
                f"{'':>8} {'':>8} {'':>10}  compile"
            )
            err = (p.stderr or p.stdout)[-400:]
            log(err)
            continue
        os.chmod(out_bin, 0o755)
        sz = out_bin.stat().st_size
        timeout = None
        if name.startswith("xu") and name != XU_BASE and bench in xu_base_s:
            # Unoptimized references may legitimately be much slower than a
            # newly optimized product build. Allow ordinary runner jitter;
            # the timeout detects hangs, while stdout checks detect errors.
            timeout = max(xu_base_s[bench] * 5.0, 30.0)
        try:
            st = timed_runs(
                str(out_bin),
                args.iters,
                discard_first=args.discard_first,
                sample_interval_s=sample_s,
                timeout_s=timeout,
                cwd=run_dirs[bench],
                before_run=(lambda: wait_for_loopback_capacity(BY_NAME[bench].loopback_connections)) if BY_NAME[bench].loopback_connections else None,
            )
        except SystemExit as e:
            log(
                f"{name:<22} {bench:<14} {'FAIL':>8} {'':>8} "
                f"{'':>8} {'':>8} {sz:10d}  {e}"
            )
            fail_mismatch = True
            continue
        if name == XU_BASE:
            xu_base_s[bench] = st.med_s
        exp = BY_NAME[bench].expect
        actual_stdout = st.stdout.replace("\r\n", "\n")
        expected_stdout = exp.replace("\r\n", "\n")
        ok = "OK" if actual_stdout == expected_stdout else f"MISMATCH {st.stdout!r}"
        if ok != "OK":
            fail_mismatch = True
        best_ms = st.best_s * 1000
        med_ms = st.med_s * 1000
        cpu_ms = st.med_cpu_s * 1000
        spark = sparkline(st.rss_curve) if st.rss_curve else ""
        extra = f"  {spark}" if spark else ""
        log(
            f"{name:<22} {bench:<14} {best_ms:8.1f} {med_ms:8.1f} "
            f"{st.med_rss_mib:8.2f} {cpu_ms:8.1f} {sz:10d}  {ok}{extra}"
        )
        results.append(
            (
                name,
                bench,
                best_ms,
                med_ms,
                st.med_rss_mib,
                cpu_ms,
                sz,
                ok,
                st.rss_curve,
            )
        )
        if st.rss_curve:
            curves_by_bench.setdefault(bench, {})[name] = st.rss_curve
            if curves_dir is not None:
                csv_path = curves_dir / f"{bench}__{_curve_slug(name)}.csv"
                write_curve_csv(csv_path, st.rss_curve)

    skip_ct = args.skip_compile_times or args.quick
    if not skip_ct:
        log("")
        log("## compile (already-built compilers, best-of-5)")
        log(f"{'impl':<22} {'bench':<14} {'best_ms':>8}")
        compile_jobs: list[tuple[str, str, list[str]]] = []
        for bench in selected:
            for _level, label, flags, tag in XU_LEVELS:
                compile_jobs.append(
                    (
                        label,
                        bench.name,
                        xu_compile_argv(
                            xu_src(bench.name),
                            flags,
                            tmp / f"ct_xu_{bench.name}_{tag}",
                        ),
                    )
                )
            if "go" in bench.langs and tools["go"] and not cross_arch:
                compile_jobs.append(
                    (
                        "go build",
                        bench.name,
                        [
                            "go",
                            "build",
                            "-o",
                            str(tmp / f"ct_go_{bench.name}"),
                            *peer_sources(bench.name, "go"),
                        ],
                    )
                )
            if "c" in bench.langs and tools["cc"]:
                for _level, label, flags, tag in c_levels:
                    compile_jobs.append(
                        (
                            label,
                            bench.name,
                            [
                                c_name,
                                *clang_arch_flags,
                                *flags,
                                "-o",
                                str(tmp / f"ct_c_{bench.name}_{tag}"),
                                str(cross_src(bench.name, "c")),
                            ],
                        )
                    )
            if "rs" in bench.langs and tools["rustc"] and not cross_arch:
                for _level, label, flags, tag in RUST_LEVELS:
                    compile_jobs.append(
                        (
                            label,
                            bench.name,
                            [
                                "rustc",
                                *flags,
                                "-o",
                                str(tmp / f"ct_rs_{bench.name}_{tag}"),
                                str(cross_src(bench.name, "rs")),
                            ],
                        )
                    )
            if "swift" in bench.langs and tools["swiftc"] and not cross_arch:
                compile_jobs.append(
                    (
                        "swiftc -O",
                        bench.name,
                        [
                            "swiftc",
                            *swift_cache_flags,
                            "-O",
                            "-o",
                            str(tmp / f"ct_sw_{bench.name}"),
                            *peer_sources(bench.name, "swift"),
                        ],
                    )
                )
        for name, bench, cmd in compile_jobs:
            try:
                ms = best_compile(cmd, COMPILE_ITERS) * 1000
                log(f"{name:<22} {bench:<14} {ms:8.1f}")
            except SystemExit as exc:
                fail_mismatch = True
                log(f"{name:<22} {bench:<14} {'FAIL':>8}  {exc}")

    SIZE_PEERS = (
        "Xu",
        "go build",
        *(label for _level, label, _flags, _tag in c_levels),
        "rustc -O1",
        "rustc -O2",
        "rustc -O3",
        "swiftc -O",
    )

    def size_rows(bench_name: str) -> list[tuple[str, int]]:
        return [
            (n, sz)
            for n, b, _best, _med, _rss, _cpu, sz, ok, _c in results
            if b == bench_name and ok == "OK"
        ]

    log("")
    log("## binary size (on-disk, not stripped)")
    log(
        f"{'impl':<22} {'bench':<14} {'bytes':>10} {'KiB':>8} {'vs Xu':>8}"
    )
    for bench in selected:
        rows = size_rows(bench.name)
        xu_sz = next((sz for n, sz in rows if n == XU_BASE), None)
        for n, sz in rows:
            kib = sz / 1024.0
            if xu_sz and sz > 0:
                rel = f"{xu_sz / sz:8.2f}×"
            else:
                rel = f"{'':>8}"
            log(f"{n:<22} {bench.name:<14} {sz:10d} {kib:8.1f} {rel}")

    log("")
    log(
        "## binary size summary  "
        "(Xu / C / Rust O1–O3 plus Go / Swift, KiB, not stripped)"
    )
    hdr = f"{'bench':<16}" + "".join(f"{p:>12}" for p in SIZE_PEERS)
    log(hdr)
    for bench in selected:
        rows = {n: sz for n, sz in size_rows(bench.name)}
        cells = []
        for p in SIZE_PEERS:
            if p in rows:
                cells.append(f"{rows[p] / 1024.0:12.1f}")
            else:
                cells.append(f"{'—':>12}")
        log(f"{bench.name:<16}" + "".join(cells))

    log("")
    log(f"## vs {XU_BASE} by bench  (time/RSS/CPU/size ratios on median)")
    for bench in selected:
        xu_row = next(
            (
                (best, med, rss, cpu, sz)
                for n, b, best, med, rss, cpu, sz, ok, _c in results
                if n == XU_BASE and b == bench.name and ok == "OK"
            ),
            None,
        )
        if xu_row is None:
            continue
        xu_best, xu_med, xu_rss, xu_cpu, xu_sz = xu_row
        log("")
        log(f"### {bench.name}  ({bench.face})")
        for n, b, best_ms, med_ms, rss_mib, cpu_ms, sz, ok, _c in results:
            if b != bench.name or ok != "OK":
                continue
            def fmt_ratio(val_xu, val_peer, label):
                if val_xu > 0 and val_peer > 0:
                    return f"{label} {val_xu / val_peer:.2f}×"
                return f"{label}     — "

            t_str = fmt_ratio(xu_med, med_ms, "wall")
            r_str = fmt_ratio(xu_rss, rss_mib, "rss")
            c_str = fmt_ratio(xu_cpu, cpu_ms, "cpu")
            s_str = fmt_ratio(xu_sz, sz, "size")
            log(
                f"{n:<22} wall med {med_ms:8.1f} best {best_ms:8.1f} ms  "
                f"rss {rss_mib:6.2f} MiB  cpu {cpu_ms:8.1f} ms  "
                f"size {sz:8d}  |  "
                f"Xu {t_str}  {r_str}  {c_str}  {s_str}"
            )

    if curves_dir is not None and curves_by_bench:
        log("")
        log("## RSS curves")
        curves_dir.mkdir(parents=True, exist_ok=True)
        for bench_name, series in curves_by_bench.items():
            svg = curves_dir / f"{bench_name}.svg"
            write_rss_svg(svg, series, title=f"{bench_name} RSS over time")
            log(f"  {svg}  ({len(series)} series)")
            for impl, curve in series.items():
                log(
                    f"    {impl:<22} n={len(curve):4d}  "
                    f"peak={max(r for _t, r in curve):.2f} MiB  "
                    f"{sparkline(curve)}"
                )
        log(f"# curves dir: {curves_dir}")

    text = "\n".join(lines) + "\n"
    Path(args.out).write_text(text, encoding="utf-8")
    log(f"\n# wrote {args.out}")
    log(f"# bins in {tmp}")
    if fail_mismatch:
        log("# FAIL: compile error, stdout MISMATCH, or timeout")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
