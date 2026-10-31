// Osprey (MIT): benchmarks/cases/gcdsum; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Recursive Euclidean GCD: sum gcd(i,1234567), 1 <= i < 2000000.
#include <stdint.h>
#include <stdio.h>


static int64_t gcd(int64_t a, int64_t b) {
    if (b == 0) { return a; }
    return gcd(b, a % b);
}

int main(void) {
    int64_t result = 0;
    int64_t i = 1;
    while (i < 2000000) {
        result += gcd(i, 1234567);
        i += 1;
    }
    printf("%lld\n", (long long)result);
    return 0;
}
