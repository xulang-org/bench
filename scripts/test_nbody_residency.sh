#!/usr/bin/env bash
# Product-only regression for golden energy and default/no-opt CPU comparison.
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
help=$("$PRODUCT_COMPILER_RUNNER" "$XU" build --help)
for mode in default no-opt; do
    set --
    if [ "$mode" = no-opt ]; then set -- --no-opt; fi
    if [[ "$help" == *--timings* ]]; then set -- "$@" --timings; fi
    "$PRODUCT_COMPILER_RUNNER" "$XU" build \
        "$BENCH_ROOT/tests/bench/game/nbody.xu" "$@" -o "$tmp/$mode" \
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
modes = ["default", "no-opt"]
golden = b"-0.169075164\n-0.169087605\n"
perf_golden = b"-0.169075164\n-0.169096567\n"
residency = {}
for mode in modes:
    sample = run_one([str(work / mode), "1000"], timeout_s=10)
    assert sample.returncode == 0 and sample.stdout == golden, (mode, sample)
    if mode == "default":
        line = next((line for line in (work / (mode + ".log")).read_text().splitlines()
                     if line.startswith("ra-fn: label=_xu_main_advance ")), None)
        if line is None:
            print("nbody: compiler did not report register residency")
            continue
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
assert medians["default"]["cpu_ms"] <= medians["no-opt"]["cpu_ms"] * 0.90, medians
report = {"lane": "product", "compiler": compiler,
          "sha256": hashlib.sha256(Path(compiler).read_bytes()).hexdigest(),
          "n": 500000, "rounds": 7, "golden": "PASS", "residency": residency,
          "medians": medians, "status": "PASS"}
if output:
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(report, indent=2) + "\n")
for mode, median in medians.items():
    print(f"nbody {mode}: CPU {median['cpu_ms']:.2f}ms wall {median['wall_ms']:.2f}ms")
checks = "golden, GPR/FP homes, paired CPU" if residency else "golden and paired CPU"
print(f"test_nbody_residency: PASS lane=product ({checks})")
PY
