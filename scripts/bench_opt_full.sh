#!/usr/bin/env bash
# One-command O0–O3 comparison: runtime + RSS/CPU/size/curves + compile + Xu --timings.
#
# Writes reports/bench_opt_levels.latest.txt and .curves/.
# Extra args are forwarded to bench_opt_levels.sh (e.g. --benches=loop_sum).
#
#   ./scripts/bench_opt_full.sh
#   make bench-opt-full
#   ./scripts/bench_opt_full.sh --benches=loop_sum,sort_lcg
#   ./scripts/bench_opt_full.sh --digest          # print latest tables, no rerun
#   ./scripts/bench_opt_full.sh --timings-only    # splice Xu --timings into latest
set -euo pipefail
cd "$(dirname "$0")/.."

# BOUNDARY: this full O0–O3 appendix is an oracle diagnostic by default; the
# product compiler must be supplied explicitly through bench_opt_levels.sh.
LANE="oracle"

SNAPSHOT="${BENCH_OPT_SNAPSHOT:-reports/bench_opt_levels.latest.txt}"

if [ "${1:-}" = "--digest" ] || [ "${1:-}" = "--timings-only" ]; then
    mode="$1"
    shift
    if [ "$mode" = "--digest" ]; then
        python3 scripts/bench_opt_full.py --digest --snapshot "$SNAPSHOT"
        exit $?
    fi
    echo "bench_opt_full: Xu --timings only → $SNAPSHOT"
    python3 scripts/bench_opt_full.py --append-timings --digest --snapshot "$SNAPSHOT"
    exit $?
fi

echo "bench_opt_full: runtime + resources + compile → $SNAPSHOT"
./scripts/bench_opt_levels.sh --save "$@" \
    || { echo "bench_opt_full: opt-levels sweep failed" >&2; exit 1; }

echo "bench_opt_full: Xu --timings (load/parse/check/mir/emit/bin)…"
python3 scripts/bench_opt_full.py --append-timings --snapshot "$SNAPSHOT" \
    || { echo "bench_opt_full: timings appendix failed" >&2; exit 1; }

echo
echo "======== digest ========"
python3 scripts/bench_opt_full.py --digest --snapshot "$SNAPSHOT"
echo "======== snapshot: $SNAPSHOT ========"
echo "curves: ${SNAPSHOT}.curves/"
echo "re-run: ./scripts/bench_opt_full.sh   or   make bench-opt-full"
