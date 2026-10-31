// Osprey (MIT): benchmarks/cases/mergesort; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Top-down merge sort with alternating split and fresh growable vectors.
// 8 rounds x 2000 values; seed=1+131*t, rank-weighted modular checksum.
// Identical split/merge/push loops in all ports; see tests/bench/osprey/README.md.

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

static Vec merge(const Vec *left, const Vec *right) {
    Vec result = {NULL, 0, 0};
    int64_t i = 0;
    int64_t j = 0;
    while (i < left->len && j < right->len) {
        if (right->data[j] < left->data[i]) {
            push(&result, right->data[j]);
            j += 1;
        } else {
            push(&result, left->data[i]);
            i += 1;
        }
    }
    while (i < left->len) { push(&result, left->data[i]); i += 1; }
    while (j < right->len) { push(&result, right->data[j]); j += 1; }
    return result;
}

static Vec merge_sort(const Vec *xs) {
    if (xs->len < 2) {
        Vec result = {NULL, 0, 0};
        int64_t i = 0;
        while (i < xs->len) { push(&result, xs->data[i]); i += 1; }
        return result;
    }
    Vec evens = {NULL, 0, 0};
    Vec odds = {NULL, 0, 0};
    int64_t i = 0;
    while (i < xs->len) { push(&evens, xs->data[i]); i += 2; }
    i = 1;
    while (i < xs->len) { push(&odds, xs->data[i]); i += 2; }
    Vec left = merge_sort(&evens);
    Vec right = merge_sort(&odds);
    Vec result = merge(&left, &right);
    free(evens.data);
    free(odds.data);
    free(left.data);
    free(right.data);
    return result;
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
        Vec sorted = merge_sort(&xs);
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
