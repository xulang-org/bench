// Osprey (MIT): benchmarks/cases/pascal; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Unmemoised Pascal recursion: binomial coefficient C(27,13).
#include <stdint.h>
#include <stdio.h>


static int64_t binom(int64_t n, int64_t k) {
    if (k == 0) { return 1; }
    if (k == n) { return 1; }
    return binom(n - 1, k - 1) + binom(n - 1, k);
}

int main(void) {
    int64_t result = binom(27, 13);
    printf("%lld\n", (long long)result);
    return 0;
}
