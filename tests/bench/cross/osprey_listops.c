// Osprey (MIT): benchmarks/cases/listops; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct { int64_t *data; int64_t len, cap; } Vec;

static void push(Vec *xs, int64_t v) {
    if (xs->len == xs->cap) {
        int64_t cap = xs->cap == 0 ? 8 : xs->cap * 2;
        int64_t *data = realloc(xs->data, (size_t)cap * sizeof(int64_t));
        if (!data) { exit(1); }
        xs->data = data;
        xs->cap = cap;
    }
    xs->data[xs->len] = v;
    xs->len += 1;
}

static int64_t hash_at(int64_t seed, int64_t i) {
    return (((seed + i) * 16807) % 2147483647 * 16807) % 2147483647;
}

static int64_t sum_list(const Vec *xs, int64_t i) {
    if (i == xs->len) { return 0; }
    return xs->data[i] + sum_list(xs, i + 1);
}

static int64_t below_list(const Vec *xs, int64_t i) {
    if (i == xs->len) { return 0; }
    int64_t add = 0;
    if (xs->data[i] < 500) { add = 1; }
    return add + below_list(xs, i + 1);
}

int main(void) {
    int64_t total = 0;
    int64_t t = 0;
    while (t < 8) {
        Vec xs = {NULL, 0, 0};
        int64_t i = 0;
        while (i < 4000) {
            push(&xs, hash_at(1 + t * 131, i) % 1000);
            i += 1;
        }
        total = (total + sum_list(&xs, 0) + below_list(&xs, 0)) % 1000000007;
        free(xs.data);
        t += 1;
    }
    printf("%lld\n", (long long)total);
    return 0;
}
