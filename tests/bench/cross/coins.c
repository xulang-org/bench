// Osprey (MIT): benchmarks/cases/coins; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Unmemoised SICP change counting: amount 600, denominations 1/5/10/25/50.
#include <stdint.h>
#include <stdio.h>


static int64_t coin(int64_t k) {
    if (k == 1) { return 1; }
    if (k == 2) { return 5; }
    if (k == 3) { return 10; }
    if (k == 4) { return 25; }
    return 50;
}
static int64_t ways(int64_t amount, int64_t kind) {
    if (amount == 0) { return 1; }
    if (amount < 0) { return 0; }
    if (kind == 0) { return 0; }
    return ways(amount - coin(kind), kind) + ways(amount, kind - 1);
}

int main(void) {
    int64_t result = ways(600, 5);
    printf("%lld\n", (long long)result);
    return 0;
}
