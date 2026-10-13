#!/usr/bin/env bash
# M186: compile-benchmark harness for bootstrap vs Gen1 self-compile.
set -euo pipefail
BENCH_ROOT=$(cd "$(dirname "$0")/.." && pwd -P)
ROOT=$(cd "${XU_ROOT:-$BENCH_ROOT/../xu}" && pwd -P)
BOOTSTRAP_ROOT=$("$ROOT/scripts/xu_host_seed.sh" --bootstrap-root)
export XU_ROOT="$ROOT"
cd "$ROOT"

# BOUNDARY: this benchmark is an oracle/primer diagnostic.  Its Rust
# bootstrap timings are useful for comparison only and are never product
# self-host evidence.
LANE="oracle"
echo "bench_compile: lane=oracle (bootstrap primer diagnostic; non-product evidence)" >&2

BASELINE="${BENCH_BASELINE:-$BENCH_ROOT/reports/bench_compile.baseline.txt}"
THRESHOLD="${BENCH_REGRESS_PCT:-5}"

. ./scripts/gen1_sources.sh || { echo "bench_compile: could not load scripts/gen1_sources.sh"; exit 1; }
ALL="$GEN1_PARSE"

cargo build --quiet --manifest-path "$BOOTSTRAP_ROOT/Cargo.toml" -p xu --bin xu 2>/dev/null || {
  echo "bench_compile: bootstrap build failed"; exit 1;
}
XU="$BOOTSTRAP_ROOT/target/debug/xu"
XU=$(XU_ALLOW_ORACLE_SEED=1 XU_REQUIRE_FROZEN_PRIMER=1 XU_SEED="$XU" \
  "$ROOT/scripts/xu_host_seed.sh") || {
  echo "bench_compile: bootstrap compiler is not the canonical frozen primer" >&2
  exit 1
}

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

echo "bench_compile: bootstrap (Rust debug) compiling Gen1 sources..."
/usr/bin/time -p sh -c "$XU -O0 --timings $GEN1_SRCS -o $tmp/gen1.xin 2>&1" 2>"$tmp/boot.time" | tee "$tmp/boot.timings"
grep '^timings:' "$tmp/boot.timings" | tail -1 > "$tmp/boot.line" || true

chmod +x "$tmp/gen1.xin"

echo "bench_compile: Gen1 self-compile (slow)..."
/usr/bin/time -p sh -c "$tmp/gen1.xin build --timings $GEN1_SRCS -o $tmp/gen2 2>&1" 2>"$tmp/gen1.time" | tee "$tmp/gen1.timings"
grep '^timings:' "$tmp/gen1.timings" | tail -1 > "$tmp/gen1.line" || true

{
  echo "# bench_compile $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lane=$LANE"
  echo "bootstrap_wall=$(grep real "$tmp/boot.time" | awk '{print $2}')"
  echo "gen1_wall=$(grep real "$tmp/gen1.time" | awk '{print $2}')"
  echo "bootstrap_timings=$(cat "$tmp/boot.line" 2>/dev/null || echo n/a)"
  echo "gen1_timings=$(cat "$tmp/gen1.line" 2>/dev/null || echo n/a)"
} | tee "$tmp/report.txt"

if [[ -f "$BASELINE" ]]; then
  python3 scripts/compile_baseline_identity.py "$BASELINE" || exit 1
  old=$(grep '^gen1_wall=' "$BASELINE" | cut -d= -f2 || echo 0)
  new=$(grep '^gen1_wall=' "$tmp/report.txt" | cut -d= -f2)
  if awk -v o="$old" -v n="$new" -v t="$THRESHOLD" 'BEGIN{ if (o>0 && n>o*(1+t/100)) exit 1; else exit 0 }'; then
    echo "bench_compile: PASS (gen1 wall ${new}s vs baseline ${old}s)"
  else
    echo "bench_compile: REGRESSION gen1 wall ${new}s > baseline ${old}s + ${THRESHOLD}%"
    exit 1
  fi
else
  echo "bench_compile: no baseline at $BASELINE — explicit calibration required" >&2
  exit 1
fi
