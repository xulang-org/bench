// Osprey (MIT): benchmarks/cases/coprime; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Osprey coprime: 2000x2000 grid, recursive Euclidean GCD.
#include <stdint.h>
#include <stdio.h>


static int64_t gcd(int64_t a, int64_t b) {
    if (b == 0) { return a; }
    return gcd(b, a % b);
}

int main(void) {
    int64_t result = 0;
    int64_t i = 2000;
    while (i > 0) {
        int64_t j = 2000;
        while (j > 0) {
            if (gcd(i, j) == 1) { result += 1; }
            j -= 1;
        }
        i -= 1;
    }
    printf("%lld\n", (long long)result);
    return 0;
}
