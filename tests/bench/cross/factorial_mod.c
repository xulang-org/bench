// Osprey (MIT): benchmarks/cases/factorial; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Product 1..10000000 modulo 1000000007; dependent multiply/remainder fold.
#include <stdint.h>
#include <stdio.h>


int main(void) {
    int64_t result = 1;
    int64_t i = 1;
    while (i <= 10000000) {
        result = (result * i) % 1000000007;
        i += 1;
    }
    printf("%lld\n", (long long)result);
    return 0;
}
