// Osprey (MIT): benchmarks/cases/collatz; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Recursive Collatz stopping times, summed over 1..100000.
#include <stdint.h>
#include <stdio.h>


static int64_t steps(int64_t n) {
    if (n == 1) { return 0; }
    if (n % 2 == 0) { return 1 + steps(n / 2); }
    return 1 + steps(3 * n + 1);
}

int main(void) {
    int64_t result = 0;
    int64_t i = 1;
    while (i <= 100000) {
        result += steps(i);
        i += 1;
    }
    printf("%lld\n", (long long)result);
    return 0;
}
