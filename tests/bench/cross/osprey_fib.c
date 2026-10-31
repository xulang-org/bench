// Osprey (MIT): benchmarks/cases/fib; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Osprey fib: naive fib(35), including the original two base cases.
#include <stdint.h>
#include <stdio.h>


static int64_t add(int64_t a, int64_t b) { return a + b; }
static int64_t sub(int64_t a, int64_t b) { return a - b; }
static int64_t fib(int64_t n) {
    if (n == 0) { return 0; }
    if (n == 1) { return 1; }
    return add(fib(sub(n, 1)), fib(sub(n, 2)));
}

int main(void) {
    int64_t result = fib(35);
    printf("%lld\n", (long long)result);
    return 0;
}
