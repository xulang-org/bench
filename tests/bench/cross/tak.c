// Osprey (MIT): benchmarks/cases/tak; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Takeuchi tak(32,16,8): ternary recursion with recursive arguments.
#include <stdint.h>
#include <stdio.h>


static int64_t sub(int64_t a, int64_t b) { return a - b; }
static int64_t tak(int64_t x, int64_t y, int64_t z) {
    if (x > y) {
        return tak(tak(sub(x, 1), y, z), tak(sub(y, 1), z, x), tak(sub(z, 1), x, y));
    }
    return z;
}

int main(void) {
    int64_t result = tak(32, 16, 8);
    printf("%lld\n", (long long)result);
    return 0;
}
