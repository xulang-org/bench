#!/usr/bin/env bash
# Measure standard-library hot-path benchmarks (os/io/fs/path/time/strings/...).
#
# Usage:
#   ./scripts/bench_stdlib.sh
#   ./scripts/bench_stdlib.sh --save
#   ./scripts/bench_stdlib.sh --check
#   ./scripts/bench_stdlib.sh --iters=5 --src-dir tests/bench/stdlib
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    echo "bench_stdlib: wrapper for scripts/bench_stdlib.py"
    echo "Examples:"
    echo "  ./scripts/bench_stdlib.sh --save"
    echo "  ./scripts/bench_stdlib.sh --check"
    echo "  XU_BENCH_ITERS=5 ./scripts/bench_stdlib.sh --discard-first"
    exit 0
fi

HAS_ITERS=0
for a in "$@"; do
    case "$a" in
        --iters|--iters=*) HAS_ITERS=1 ;;
    esac
done

set -- \
    "--iters" "${XU_BENCH_ITERS:-7}" \
    "$@"

if [ "$HAS_ITERS" -eq 1 ] && [ "$#" -gt 2 ]; then
    # drop the injected default when caller passed explicit --iters.
    # Pattern: [--iters v] <user args>, detect the first pair and remove it.
    if [ "$1" = "--iters" ]; then
        shift 2
    fi
fi

python3 scripts/bench_stdlib.py "$@"
