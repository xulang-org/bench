#!/usr/bin/env bash
set -euo pipefail
BENCH_ROOT=$(cd "$(dirname "$0")/.." && pwd -P)
ROOT=$(cd "${XU_ROOT:-$BENCH_ROOT/../xu}" && pwd -P)
export XU_ROOT="$ROOT"
export PYTHONPATH="$BENCH_ROOT/scripts${PYTHONPATH:+:$PYTHONPATH}"
cd "$ROOT"

LANE="product"
HOST_SEED_RESOLVER="$PWD/scripts/xu_host_seed.sh"
PRODUCT_COMPILER_RUNNER="$PWD/scripts/run_product_compiler.sh"

MODE="run"
ITERS="${XU_BENCH_ITERS:-5}"
GEN3_INPUT=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --save) MODE="save" ;;
        --check) MODE="check" ;;
        --iters=*) ITERS="${1#*=}" ;;
        --xu=*) GEN3_INPUT="${1#*=}" ;;
        --xu)
            shift
            [ "$#" -gt 0 ] || { echo "bench_runtime: --xu needs a path"; exit 1; }
            GEN3_INPUT="$1"
            ;;
        *) echo "bench_runtime: unknown arg $1"; exit 1 ;;
    esac
    shift
done

if [ -n "$GEN3_INPUT" ]; then
    if ! GEN3=$(XU_SEED="$GEN3_INPUT" "$HOST_SEED_RESOLVER"); then
        echo "bench_runtime: --xu must name a hosted product compiler (use bin/xu or a hosted snapshot)" >&2
        exit 1
    fi
else
    if ! GEN3=$("$HOST_SEED_RESOLVER"); then
        echo "bench_runtime: no hosted product compiler; run make xu or pass --xu=..." >&2
        exit 1
    fi
fi
[ -x "$GEN3" ] || { echo "bench_runtime: compiler is not executable: $GEN3"; exit 1; }
GEN3_LANE="product"
echo "bench_runtime: lane=product (O0 vs default optimization)" >&2

compile_product() {
    # Keep the compiler boundary in one place.  This also clears ambient
    # XUPATH/XU_CACHE and rejects a primer even when a caller supplied a
    # symlink or a relative path.
    "$PRODUCT_COMPILER_RUNNER" "$GEN3" build "$@"
}

BASELINE="$BENCH_ROOT/reports/bench_runtime.baseline.txt"
mkdir -p "$(dirname "$BASELINE")"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

cat > "$tmp/timer.py" <<'PY'
import subprocess, sys, time
path, n, cwd = sys.argv[1], int(sys.argv[2]), sys.argv[3]
best = None
out = b""
for _ in range(n):
    t0 = time.perf_counter()
    p = subprocess.run([path], capture_output=True, cwd=cwd)
    dt = time.perf_counter() - t0
    if p.returncode != 0:
        sys.stderr.write("run failed rc=%d\n" % p.returncode)
        sys.exit(3)
    out = p.stdout
    if best is None or dt < best:
        best = dt
sys.stdout.write(out.decode())
sys.stderr.write("%d\n" % int(best * 1000))
PY

echo "bench_runtime: xu=$GEN3 iters=$ITERS (best-of) host=$(uname -sm)"
printf "%-16s %12s %12s %8s  %s\n" "bench" "O0_ms" "product_ms" "ratio" "checksum"

fail=0
compat=0
lines=""
for src in "$BENCH_ROOT"/tests/bench/*.xu; do
    name=$(basename "$src" .xu)
    run_dir="$tmp/run/$name"
    mkdir -p "$run_dir"
    if ! "$PRODUCT_COMPILER_RUNNER" "$GEN3" build -O0 "$src" -o "$tmp/${name}_boot.bin" 2>"$tmp/${name}.cerr"; then
        echo "$name: O0 compile FAIL"; head -2 "$tmp/${name}.cerr"; fail=1; continue
    fi
    if ! compile_product "$src" -o "$tmp/${name}_gen3.bin" 2>>"$tmp/${name}.cerr"; then
        echo "$name: gen3 compile FAIL"; head -2 "$tmp/${name}.cerr"; fail=1; continue
    fi
    chmod +x "$tmp/${name}_gen3.bin"
    ck=OK
    ms_b="-"
    chmod +x "$tmp/${name}_boot.bin"
    out_b=$(python3 "$tmp/timer.py" "$tmp/${name}_boot.bin" "$ITERS" "$run_dir" 2>"$tmp/${name}_boot.ms") \
        || { echo "$name: O0 run FAIL"; fail=1; continue; }
    ms_b=$(cat "$tmp/${name}_boot.ms")
    out_g=$(python3 "$tmp/timer.py" "$tmp/${name}_gen3.bin" "$ITERS" "$run_dir" 2>"$tmp/${name}_gen3.ms") \
        || { echo "$name: gen3 run FAIL"; fail=1; continue; }
    ms_g=$(cat "$tmp/${name}_gen3.ms")
    sum_b=$(printf '%s' "$out_b" | shasum | cut -c1-12)
    sum_g=$(printf '%s' "$out_g" | shasum | cut -c1-12)
    if [ "$out_b" != "$out_g" ]; then
        ck="MISMATCH"
        fail=1
    fi
    ratio="-"
    ratio=$(awk -v b="$ms_b" -v g="$ms_g" 'BEGIN{ if (b > 0) printf "%.2f", g / b; else print "-" }')
    printf "%-16s %12s %12s %8s  %s\n" "$name" "$ms_b" "$ms_g" "$ratio" "$ck"
    lines="${lines}${name} boot=${ms_b} gen3=${ms_g} sha=${sum_b}
"
    if [ "$MODE" = "check" ] && [ -f "$BASELINE" ]; then
        # New benches need not have a historical entry. A no-match grep
        # under errexit/pipefail used to abort the entire sweep silently.
        base_g=$(sed -n "/^${name} /s/.*gen3=\([0-9]*\).*/\1/p" "$BASELINE")
        base_sha=$(sed -n "/^${name} /s/.*sha=\([0-9a-f]*\).*/\1/p" "$BASELINE")
        if [ -z "$base_g" ] && [ -z "$base_sha" ]; then
            echo "  NO_BASELINE: $name (output checked; historical regression unavailable)"
        fi
        if [ -n "$base_sha" ] && [ "$base_sha" != "$sum_b" ]; then
            echo "  REGRESSION: $name output checksum changed vs baseline"
            fail=1
        fi
        if [ -n "$base_g" ] && [ "$base_g" -gt 0 ]; then
            if awk -v b="$base_g" -v n="$ms_g" 'BEGIN{ exit (n > b * 1.30) ? 0 : 1 }'; then
                echo "  REGRESSION: $name gen3 ${ms_g}ms > baseline ${base_g}ms +30%"
                fail=1
            fi
        fi
    fi
done


if [ "$MODE" = "save" ]; then
    {
        echo "# bench_runtime baseline — $(date '+%Y-%m-%d') host: $(uname -sm)"
        echo "# lane=product (O0 vs default optimization)"
        echo "# Fields: name boot=<ms> gen3=<ms> sha=<output checksum>. Re-record"
        echo "# (scripts/bench_runtime.sh --save) only after intended codegen changes."
        printf '%s' "$lines"
    } > "$BASELINE"
    echo "bench_runtime: baseline written to $BASELINE"
fi

exit $fail
