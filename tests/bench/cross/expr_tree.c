// Osprey (MIT): benchmarks/cases/exprtree; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct Expr { int64_t tag, value; struct Expr *left, *right; } Expr;

static int64_t hash_at(int64_t seed, int64_t idx) {
    return (((seed + idx) * 16807) % 2147483647 * 16807) % 2147483647;
}

static Expr *build(int64_t seed, int64_t idx, int64_t depth) {
    Expr *e = malloc(sizeof *e);
    if (!e) { exit(1); }
    if (depth == 0) {
        *e = (Expr){0, hash_at(seed, idx) % 1000, NULL, NULL};
    } else {
        Expr *left = build(seed, idx * 2 + 1, depth - 1);
        Expr *right = build(seed, idx * 2 + 2, depth - 1);
        *e = (Expr){1 + hash_at(seed, idx) % 2, 0, left, right};
    }
    return e;
}

static int64_t eval(const Expr *e) {
    if (e->tag == 0) { return e->value; }
    int64_t left = eval(e->left);
    int64_t right = eval(e->right);
    if (e->tag == 1) { return (left + right) % 1000000007; }
    return (left * right) % 1000000007;
}

static void destroy(Expr *e) {
    if (e->tag != 0) { destroy(e->left); destroy(e->right); }
    free(e);
}

int main(void) {
    int64_t total = 0;
    int64_t t = 0;
    while (t < 10) {
        Expr *expr = build(1 + t * 7, 1, 14);
        total = (total + eval(expr)) % 1000000007;
        destroy(expr);
        t += 1;
    }
    printf("%lld\n", (long long)total);
    return 0;
}
