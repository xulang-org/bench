#!/usr/bin/env bash
set -euo pipefail
BENCH_ROOT=$(cd "$(dirname "$0")/.." && pwd -P)
ROOT=$(cd "${XU_ROOT:-$BENCH_ROOT/../xu}" && pwd -P)
export XU_ROOT="$ROOT"
cd "$ROOT"

LANE="product"

BASELINE="${BENCH_BASELINE:-$BENCH_ROOT/reports/bench_compile.baseline.txt}"
THRESHOLD="${BENCH_REGRESS_PCT:-5}"

. ./scripts/gen1_sources.sh || { echo "bench_compile: could not load scripts/gen1_sources.sh"; exit 1; }
ALL="$GEN1_PARSE"

XU=$("$ROOT/scripts/xu_host_seed.sh")

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

echo "bench_compile: hosted seed compiling next compiler..."
/usr/bin/time -p "$ROOT/scripts/run_product_compiler.sh" "$XU" build --timings $GEN1_SRCS -o "$tmp/gen1.xin" >"$tmp/boot.timings" 2>"$tmp/boot.time"
grep '^timings:' "$tmp/boot.timings" "$tmp/boot.time" | tail -1 > "$tmp/boot.line" || true

chmod +x "$tmp/gen1.xin"

echo "bench_compile: Gen1 self-compile (slow)..."
/usr/bin/time -p "$ROOT/scripts/run_product_compiler.sh" "$tmp/gen1.xin" build --timings $GEN1_SRCS -o "$tmp/gen2" >"$tmp/gen1.timings" 2>"$tmp/gen1.time"
grep '^timings:' "$tmp/gen1.timings" "$tmp/gen1.time" | tail -1 > "$tmp/gen1.line" || true

{
  echo "# bench_compile $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "lane=$LANE"
  echo "seed_wall=$(grep real "$tmp/boot.time" | awk '{print $2}')"
  echo "gen1_wall=$(grep real "$tmp/gen1.time" | awk '{print $2}')"
  echo "seed_timings=$(cat "$tmp/boot.line" 2>/dev/null || echo n/a)"
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
