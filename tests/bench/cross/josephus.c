// Osprey (MIT): benchmarks/cases/josephus; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Josephus survivor, zero-based, n=10000000 and k=7; variable divisor chain.
#include <stdint.h>
#include <stdio.h>


int main(void) {
    int64_t result = 0;
    int64_t i = 2;
    while (i <= 10000000) {
        result = (result + 7) % i;
        i += 1;
    }
    printf("%lld\n", (long long)result);
    return 0;
}
