#!/usr/bin/env bash
# Product-only regression: FieldRMW/f64 residency, golden energy, O2/O3 vs O1.
# Uses paired CPU samples so unrelated host workloads do not become wall regressions.
# Usage: scripts/test_nbody_residency.sh --xu=bin/xu [--out=/tmp/nbody.json]
set -euo pipefail
BENCH_ROOT=$(cd "$(dirname "$0")/.." && pwd -P)
ROOT=$(cd "${XU_ROOT:-$BENCH_ROOT/../xu}" && pwd -P)
cd "$ROOT"
LANE="product"
HOST_SEED_RESOLVER="$ROOT/scripts/xu_host_seed.sh"
PRODUCT_COMPILER_RUNNER="$ROOT/scripts/run_product_compiler.sh"
XU_INPUT=bin/xu
OUT=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --xu=*) XU_INPUT="${1#*=}" ;;
        --out=*) OUT="${1#*=}" ;;
        *) echo "test_nbody_residency: unknown arg $1" >&2; exit 1 ;;
    esac
    shift
done
XU=$(XU_SEED="$XU_INPUT" "$HOST_SEED_RESOLVER")
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
for mode in O1 O2 O3 nrc; do
    flag="-$mode"
    [ "$mode" != nrc ] || flag=--no-regcache
    "$PRODUCT_COMPILER_RUNNER" "$XU" build \
        "$BENCH_ROOT/tests/bench/game/nbody.xu" "$flag" --timings -o "$tmp/$mode" \
        >"$tmp/$mode.log" 2>&1
done
python3 - "$BENCH_ROOT" "$XU" "$tmp" "$OUT" <<'PY'
import hashlib
import json
import re
import statistics
import sys
from pathlib import Path

root, compiler, work, output = sys.argv[1:]
sys.path.insert(0, str(Path(root) / "scripts"))
from bench_rusage import run_one

work = Path(work)
modes = ["O1", "O2", "O3", "nrc"]
golden = b"-0.169075164\n-0.169087605\n"
perf_golden = b"-0.169075164\n-0.169096567\n"
residency = {}
for mode in modes:
    sample = run_one([str(work / mode), "1000"], timeout_s=10)
    assert sample.returncode == 0 and sample.stdout == golden, (mode, sample)
    if mode != "nrc":
        line = next(line for line in (work / (mode + ".log")).read_text().splitlines()
                    if line.startswith("ra-fn: label=_xu_main_advance "))
        fields = dict(re.findall(r"(\w+)=([^ ]+)", line))
        assert fields["mode"] == "vreg" and fields["reason"] == "verified", fields
        scalar, gpr, fp, spill = (int(fields[key]) for key in ["scalar", "gpr", "fp", "spill"])
        assert scalar == gpr + fp + spill, fields
        assert gpr > 0 and (fp > 0 or int(fields["fp_cache_pins"]) > 0), fields
        residency[mode] = fields

# Warm every binary before interleaving the seven measurement rounds.
for mode in modes:
    sample = run_one([str(work / mode), "500000"], timeout_s=30)
    assert sample.returncode == 0 and sample.stdout == perf_golden, (mode, sample)
samples = {mode: [] for mode in modes}
for round_index in range(7):
    order = modes[round_index % len(modes):] + modes[:round_index % len(modes)]
    for mode in order:
        sample = run_one([str(work / mode), "500000"], timeout_s=30)
        assert sample.returncode == 0 and sample.stdout == perf_golden, (mode, sample)
        samples[mode].append(sample)
medians = {mode: {"cpu_ms": statistics.median(s.cpu_s for s in runs) * 1000,
                  "wall_ms": statistics.median(s.wall_s for s in runs) * 1000}
           for mode, runs in samples.items()}
baseline = medians["O1"]["cpu_ms"]
for mode in ["O2", "O3"]:
    assert medians[mode]["cpu_ms"] <= baseline * 1.10 + 2, medians
assert baseline <= medians["nrc"]["cpu_ms"] * 0.90, medians
report = {"lane": "product", "compiler": compiler,
          "sha256": hashlib.sha256(Path(compiler).read_bytes()).hexdigest(),
          "n": 500000, "rounds": 7, "golden": "PASS", "residency": residency,
          "medians": medians, "status": "PASS"}
if output:
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(report, indent=2) + "\n")
for mode, median in medians.items():
    print(f"nbody {mode}: CPU {median['cpu_ms']:.2f}ms wall {median['wall_ms']:.2f}ms")
print("test_nbody_residency: PASS lane=product (golden, GPR/FP homes, paired CPU)")
PY
