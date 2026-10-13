#!/usr/bin/env bash
# O0..O3 runtime efficiency + stdout lock.
#
# Full suite (all tests/bench language-capability loads) prints best+median.
# --check without --full keeps the historical 3-bench wall-clock ruler:
#   stdout match on loop_sum / sha256_chain / sort_lcg; loop_sum O3 ≤ O2×1.1.
#
# Usage:
#   scripts/bench_opt_full.sh                   # one-command full save (runtime+RSS+compile+Xu --timings)
#   scripts/bench_opt_levels.sh                 # full suite
#   scripts/bench_opt_levels.sh --check         # gate subset
#   scripts/bench_opt_levels.sh --full --check  # checksum every bench
#   scripts/bench_opt_levels.sh --save          # Xu+clang+go+rustc+swiftc; RSS/CPU/size/curves + compile
#   scripts/bench_opt_levels.sh --skip-runtime --save  # compile wall/RSS only; splice into latest
#   scripts/bench_opt_levels.sh --no-clang      # skip Clang
#   scripts/bench_opt_levels.sh --no-go         # skip Go
#   scripts/bench_opt_levels.sh --no-rustc      # skip rustc
#   scripts/bench_opt_levels.sh --no-swiftc     # skip Swift
#   scripts/bench_opt_levels.sh --sample-ms=0   # no live RSS curves
#   XU_BENCH_ITERS=7 scripts/bench_opt_levels.sh --check
set -euo pipefail
cd "$(dirname "$0")/.."
BENCH_ROOT=$(pwd -P)
ROOT=$(cd "${XU_ROOT:-$BENCH_ROOT/../xu}" && pwd -P)
BOOTSTRAP_ROOT=$("$ROOT/scripts/xu_host_seed.sh" --bootstrap-root)
export XU_ROOT="$ROOT"
export XU_ROOT="$ROOT"
cd "$BENCH_ROOT"

PY=(python3 scripts/bench_opt_levels.py)
CHECK=0
FULL=0
QUICK=0
HAS_XU=0
XU_OVERRIDE=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --check) CHECK=1; PY+=(--check) ;;
        --save) PY+=(--save) ;;
        --full) FULL=1 ;;
        --quick) QUICK=1; PY+=(--quick) ;;
        --iters=*) PY+=(--iters "${1#*=}") ;;
        --xu=*) PY+=(--xu "${1#*=}"); XU_OVERRIDE="${1#*=}"; HAS_XU=1 ;;
        --benches=*) PY+=(--benches "${1#*=}") ;;
        --no-clang) PY+=(--no-clang) ;;
        --no-go) PY+=(--no-go) ;;
        --no-rustc) PY+=(--no-rustc) ;;
        --no-swiftc) PY+=(--no-swiftc) ;;
        --clang=*) PY+=(--clang "${1#*=}") ;;
        --go=*) PY+=(--go "${1#*=}") ;;
        --sample-ms=*) PY+=(--sample-ms "${1#*=}") ;;
        --curves-dir=*) PY+=(--curves-dir "${1#*=}") ;;
        --skip-runtime) PY+=(--skip-runtime) ;;
        --no-compile-times) PY+=(--no-compile-times) ;;
        --compile-iters=*) PY+=(--compile-iters "${1#*=}") ;;
        --list) PY+=(--list) ;;
        *) echo "bench_opt_levels: unknown arg $1" >&2; exit 1 ;;
    esac
    shift
done

if [ -n "${XU_BENCH_ITERS:-}" ]; then
    found_iters=0
    for a in "${PY[@]}"; do
        if [ "$a" = "--iters" ]; then found_iters=1; break; fi
    done
    if [ "$found_iters" = 0 ]; then
        PY+=(--iters "$XU_BENCH_ITERS")
    fi
fi

# make bench-opt-levels --check stays the 3-bench ruler unless --full.
if [ "$CHECK" = 1 ] && [ "$FULL" = 0 ] && [ "$QUICK" = 0 ]; then
    PY+=(--quick)
fi

if [ "$HAS_XU" = 0 ]; then
    # The no-override form is intentionally the frozen oracle benchmark.  A
    # caller that supplies a hosted product compiler must not trigger an
    # unrelated cargo/bootstrap build merely as a hidden fallback.
    cargo build --quiet --manifest-path "$BOOTSTRAP_ROOT/Cargo.toml" -p xu \
        || { echo "bench_opt_levels: bootstrap build failed"; exit 1; }
    # Primer is the O0–O3 ruler (matches cargo e2e). Product via --xu=bin/xu.
    LANE="oracle"
    echo "bench_opt_levels: lane=oracle (bootstrap primer default; product requires explicit --xu)" >&2
    primer=""
    for candidate in \
        "$BOOTSTRAP_ROOT/target/debug/xu" \
        "$BOOTSTRAP_ROOT/target/debug/xu.exe" \
        "$BOOTSTRAP_ROOT/target/release/xu" \
        "$BOOTSTRAP_ROOT/target/release/xu.exe"; do
        if [ -x "$candidate" ]; then
            primer=$candidate
            break
        fi
    done
    [ -n "$primer" ] || { echo "bench_opt_levels: bootstrap compiler missing after build" >&2; exit 1; }
    PY+=(--xu "$primer")
else
    # An explicit compiler override is product by default; a path naming the
    # frozen primer remains oracle so the label cannot over-claim evidence.
    case "$XU_OVERRIDE" in
        bootstrap/*|*/bootstrap/*) LANE="oracle"; echo "bench_opt_levels: lane=oracle (explicit bootstrap --xu)" >&2 ;;
        *) LANE="product"; echo "bench_opt_levels: lane=product (explicit --xu override)" >&2 ;;
    esac
fi

# Pass the lane chosen by this wrapper explicitly.  The Python driver defaults
# to oracle for its diagnostic contract and must not infer a product lane from
# a path (or silently fall back to the primer).
PY+=(--lane "$LANE")

export XUPATH="$ROOT/src${XUPATH:+:$XUPATH}"
# No exec: wrappers such as bench_opt_full.sh need to continue after --save.
"${PY[@]}"
