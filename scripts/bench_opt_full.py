#!/usr/bin/env python3
"""Helpers for scripts/bench_opt_full.sh: Xu --timings appendix + compact digest."""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench_crosslang import BENCHES, xu_src  # noqa: E402

BENCH_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("XU_ROOT", BENCH_ROOT.parent / "xu")).expanduser().resolve()
sys.path.insert(0, str(ROOT / "scripts"))
from product_compiler import resolve_product_compiler as resolve_hosted_compiler, PRODUCT_RUNNER as HOSTED_RUNNER, product_compile_argv
LANE = "product"
SNAPSHOT = BENCH_ROOT / "reports" / "bench_opt_levels.latest.txt"
TIMINGS_MARK = "## xu product --timings"
OPTS = (0, 1, 2, 3)
DIGEST_HEADINGS = (
    "## wall median ms",
    "## peak RSS median MiB",
    "## CPU median ms (user+sys)",
    "## binary bytes",
    "## compile wall median ms (already-built compiler)",
    "## compile peak RSS median MiB (compiler process)",
    TIMINGS_MARK,
)


def ensure_xupath() -> None:
    src = str(ROOT / "src")
    cur = os.environ.get("XUPATH", "")
    parts = [p for p in cur.split(":") if p]
    if src not in parts:
        os.environ["XUPATH"] = src if not cur else f"{src}:{cur}"


def parse_timings(blob: str) -> dict[str, str] | None:
    m = re.search(
        r"timings:\s*load=(\d+)ms parse=(\d+)ms check=(\d+)ms "
        r"mir=(\d+)ms emit=(\d+)ms bin=(\d+)ms total=(\d+)ms",
        blob,
    )
    if not m:
        return None
    keys = ("load", "parse", "check", "mir", "emit", "bin", "total")
    return dict(zip(keys, m.groups()))


def snapshot_benches(path: Path, xu: Path):
    from bench_snapshot_identity import metadata, compiler_sha256
    saved = metadata(path)
    if saved.get("lane") != "product":
        raise SystemExit("product snapshot required for hosted timings")
    if saved.get("xu_sha256") != compiler_sha256(xu):
        raise SystemExit("snapshot compiler SHA differs from product compiler")
    names = [n.strip() for n in saved.get("benches", "").split(",") if n.strip()]
    by_name = {b.name: b for b in BENCHES}
    if not names or any(n not in by_name for n in names):
        raise SystemExit("snapshot benches missing/unknown")
    return [by_name[n] for n in names]


def run_xu_timings(xu: Path, benches) -> str:
    ensure_xupath()
    lines = [
        f"{TIMINGS_MARK} (one shot per -On; product {xu})",
        f"{'bench':<18} {'opt':<4} "
        f"{'load':>6} {'parse':>6} {'check':>6} {'mir':>6} {'emit':>6} "
        f"{'bin':>6} {'total':>6}",
    ]
    tmp = Path(tempfile.mkdtemp(prefix="xu_opt_t_"))
    try:
        for bench in benches:
            src = xu_src(bench.name)
            if not src.is_file():
                continue
            for opt in OPTS:
                out = tmp / f"{bench.name}.O{opt}.xin"
                p = subprocess.run(
                    product_compile_argv(xu, "build", "--timings", f"-O{opt}", str(src), "-o", str(out), runner=HOSTED_RUNNER),
                    capture_output=True,
                    text=True,
                )
                blob = (p.stderr or "") + "\n" + (p.stdout or "")
                t = parse_timings(blob)
                if p.returncode != 0 or t is None:
                    err = (p.stderr or p.stdout or "fail")[-80:].replace("\n", " ")
                    lines.append(f"{bench.name:<18} O{opt:<3}  FAIL {err}")
                    continue
                lines.append(
                    f"{bench.name:<18} O{opt:<3} "
                    f"{t['load']:>6} {t['parse']:>6} {t['check']:>6} "
                    f"{t['mir']:>6} {t['emit']:>6} {t['bin']:>6} {t['total']:>6}"
                )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    lines.append("")
    lines.append(
        "# Phase times are milliseconds from one compilation per tier; "
        "compare the measured columns before attributing optimization overhead."
    )
    return "\n".join(lines) + "\n"


def splice_timings(path: Path, block: str) -> None:
    prev = path.read_text() if path.is_file() else ""
    idx = prev.find("\n" + TIMINGS_MARK)
    if idx < 0:
        idx = prev.find(TIMINGS_MARK)
    if idx >= 0:
        prev = prev[:idx].rstrip() + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prev.rstrip() + "\n\n" + block.lstrip("\n"))


def extract_section(text: str, heading: str) -> str | None:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if not line.startswith(heading):
            continue
        # Prefer the pivot table, not the long "best+median of N" detail header.
        if "best+median" in line:
            continue
        start = i
        break
    if start is None:
        return None
    out = [lines[start]]
    for line in lines[start + 1 :]:
        if line.startswith("## ") and not line.startswith(heading):
            break
        out.append(line)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out)


def digest(path: Path) -> str:
    text = path.read_text()
    chunks = []
    head = [ln for ln in text.splitlines() if ln.startswith("# ")][:16]
    if head:
        chunks.append("\n".join(head))
    for h in DIGEST_HEADINGS:
        sec = extract_section(text, h)
        if sec:
            chunks.append(sec)
    if not chunks:
        return f"(empty digest: {path})\n"
    return "\n\n".join(chunks) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    ap.add_argument("--append-timings", action="store_true")
    ap.add_argument("--digest", action="store_true")
    ap.add_argument("--xu", type=Path, default=None)
    args = ap.parse_args()
    snap = args.snapshot
    if args.append_timings:
        xu = resolve_hosted_compiler(args.xu)
        if not xu.is_file() or not os.access(xu, os.X_OK):
            print(f"bench_opt_full: missing xu {xu}", file=sys.stderr)
            return 1
        benches = snapshot_benches(snap, xu)
        block = run_xu_timings(xu, benches)
        snapshot_benches(snap, xu)
        splice_timings(snap, block)
        print(f"# spliced {TIMINGS_MARK} into {snap}", flush=True)
    if args.digest:
        if not snap.is_file():
            print(f"bench_opt_full: no snapshot {snap}", file=sys.stderr)
            return 1
        sys.stdout.write(digest(snap))
    if not args.append_timings and not args.digest:
        ap.print_help()
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
