// Osprey (MIT): benchmarks/cases/quicksort; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Osprey first-element-pivot quicksort; two partition passes and fresh vectors.
// 8 rounds x 2000 values; seed=1+131*t, rank-weighted modular checksum.
// Identical partition/concatenate/push loops in all ports; see tests/bench/osprey/README.md.

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

static Vec quicksort(const Vec *xs) {
    if (xs->len == 0) { return (Vec){NULL, 0, 0}; }
    int64_t pivot = xs->data[0];
    Vec below = {NULL, 0, 0};
    Vec at_least = {NULL, 0, 0};
    int64_t i = 1;
    while (i < xs->len) {
        if (xs->data[i] < pivot) { push(&below, xs->data[i]); }
        i += 1;
    }
    i = 1;
    while (i < xs->len) {
        if (xs->data[i] >= pivot) { push(&at_least, xs->data[i]); }
        i += 1;
    }
    Vec sorted = quicksort(&below);
    push(&sorted, pivot);
    Vec right = quicksort(&at_least);
    i = 0;
    while (i < right.len) { push(&sorted, right.data[i]); i += 1; }
    free(below.data);
    free(at_least.data);
    free(right.data);
    return sorted;
}

int main(void) {
    int64_t total = 0;
    int64_t t = 0;
    while (t < 8) {
        Vec xs = {NULL, 0, 0};
        int64_t i = 0;
        while (i < 2000) {
            push(&xs, hash_at(1 + t * 131, i) % 100000);
            i += 1;
        }
        Vec sorted = quicksort(&xs);
        int64_t weight = 0;
        i = 0;
        while (i < sorted.len) {
            weight = (weight + sorted.data[i] * (i + 1)) % 1000000007;
            i += 1;
        }
        total = (total + weight) % 1000000007;
        free(xs.data);
        free(sorted.data);
        t += 1;
    }
    printf("%lld\n", (long long)total);
    return 0;
}
