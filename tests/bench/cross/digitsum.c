// Osprey (MIT): benchmarks/cases/digitsum; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Recursive decimal digit sums, summed over 1..2000000.
#include <stdint.h>
#include <stdio.h>


static int64_t digit_sum(int64_t n) {
    if (n < 10) { return n; }
    return n % 10 + digit_sum(n / 10);
}

int main(void) {
    int64_t result = 0;
    int64_t i = 1;
    while (i <= 2000000) {
        result += digit_sum(i);
        i += 1;
    }
    printf("%lld\n", (long long)result);
    return 0;
}
