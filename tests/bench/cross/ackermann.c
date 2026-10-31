// Osprey (MIT): benchmarks/cases/ackermann; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Ackermann(3,10): nested, data-dependent recursion.
#include <stdint.h>
#include <stdio.h>


static int64_t add(int64_t a, int64_t b) { return a + b; }
static int64_t sub(int64_t a, int64_t b) { return a - b; }
static int64_t ack(int64_t m, int64_t n) {
    if (m == 0) { return add(n, 1); }
    if (n == 0) { return ack(sub(m, 1), 1); }
    return ack(sub(m, 1), ack(m, sub(n, 1)));
}

int main(void) {
    int64_t result = ack(3, 10);
    printf("%lld\n", (long long)result);
    return 0;
}
