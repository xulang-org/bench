// Osprey (MIT): benchmarks/cases/isqrt; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Integer Newton iteration, sum floor(sqrt(i)) over 1..1000000.
#include <stdint.h>
#include <stdio.h>


static int64_t root(int64_t n) {
    if (n < 2) { return n; }
    int64_t x = n;
    int64_t y = (x + n / x) / 2;
    while (y < x) {
        x = y;
        y = (x + n / x) / 2;
    }
    return x;
}

int main(void) {
    int64_t result = 0;
    int64_t i = 1;
    while (i <= 1000000) {
        result += root(i);
        i += 1;
    }
    printf("%lld\n", (long long)result);
    return 0;
}
