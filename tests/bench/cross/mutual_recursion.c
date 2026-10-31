// Osprey (MIT): benchmarks/cases/mutual; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Mutually recursive parity, i%1000 for 1 <= i < 130000.
#include <stdint.h>
#include <stdio.h>

static int64_t odd(int64_t n);

static int64_t even(int64_t n) {
    if (n == 0) { return 1; }
    return odd(n - 1);
}
static int64_t odd(int64_t n) {
    if (n == 0) { return 0; }
    return even(n - 1);
}

int main(void) {
    int64_t result = 0;
    int64_t i = 1;
    while (i < 130000) {
        result += even(i % 1000);
        i += 1;
    }
    printf("%lld\n", (long long)result);
    return 0;
}
