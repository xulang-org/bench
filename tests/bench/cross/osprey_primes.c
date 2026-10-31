// Osprey (MIT): benchmarks/cases/primes; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Osprey primes: trial division, every candidate divisor from 2 through sqrt(n).
#include <stdint.h>
#include <stdio.h>


static int64_t has_factor(int64_t n, int64_t d) {
    if (d * d > n) { return 0; }
    if (n % d == 0) { return 1; }
    return has_factor(n, d + 1);
}
static int64_t is_prime(int64_t n) {
    if (n < 2) { return 0; }
    return 1 - has_factor(n, 2);
}

int main(void) {
    int64_t result = 0;
    int64_t n = 2;
    while (n < 200000) {
        if (is_prime(n) != 0) { result += 1; }
        n += 1;
    }
    printf("%lld\n", (long long)result);
    return 0;
}
