// Osprey (MIT): benchmarks/cases/nestedloop; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Osprey nestedloop: descending 250^3 modular multiply/adds.
#include <stdint.h>
#include <stdio.h>


static int64_t loop_k(int64_t i, int64_t j, int64_t n, int64_t initial) {
    int64_t k = n;
    int64_t acc = initial;
    while (k != 0) {
        acc = (acc + i * j * k) % 1000000007;
        k -= 1;
    }
    return acc;
}
static int64_t loop_j(int64_t i, int64_t n, int64_t initial) {
    int64_t j = n;
    int64_t acc = initial;
    while (j != 0) {
        acc = loop_k(i, j, n, acc);
        j -= 1;
    }
    return acc;
}
static int64_t loop_i(int64_t n) {
    int64_t i = n;
    int64_t acc = 0;
    while (i != 0) {
        acc = loop_j(i, n, acc);
        i -= 1;
    }
    return acc;
}

int main(void) {
    int64_t result = loop_i(250);
    printf("%lld\n", (long long)result);
    return 0;
}
