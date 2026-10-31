// Osprey (MIT): benchmarks/cases/powmod; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Sum i^20 mod 1000000007, 1 <= i < 1000000; twenty multiplies, no squaring.
#include <stdint.h>
#include <stdio.h>


static int64_t power(int64_t base, int64_t e, int64_t acc) {
    if (e == 0) { return acc; }
    return power(base, e - 1, (acc * base) % 1000000007);
}

int main(void) {
    int64_t result = 0;
    int64_t i = 1;
    while (i < 1000000) {
        result = (result + power(i, 20, 1)) % 1000000007;
        i += 1;
    }
    printf("%lld\n", (long long)result);
    return 0;
}
