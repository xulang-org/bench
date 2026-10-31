// Osprey (MIT): benchmarks/cases/hanoi; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Accumulator-threaded double recursion for 25 Hanoi disks; count moves.
#include <stdint.h>
#include <stdio.h>


static int64_t moves(int64_t n, int64_t acc) {
    if (n == 0) { return acc; }
    return moves(n - 1, moves(n - 1, acc) + 1);
}

int main(void) {
    int64_t result = moves(25, 0);
    printf("%lld\n", (long long)result);
    return 0;
}
