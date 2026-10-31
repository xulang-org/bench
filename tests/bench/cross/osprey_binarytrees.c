// Osprey (MIT): benchmarks/cases/binarytrees; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct Tree { struct Tree *left, *right; } Tree;

static Tree *make(int64_t depth) {
    Tree *t = malloc(sizeof *t);
    if (!t) { exit(1); }
    if (depth == 0) { t->left = NULL; t->right = NULL; }
    else { t->left = make(depth - 1); t->right = make(depth - 1); }
    return t;
}

static int64_t check(const Tree *t) {
    if (!t) { return 0; }
    return 1 + check(t->left) + check(t->right);
}

static void destroy(Tree *t) {
    if (!t) { return; }
    destroy(t->left);
    destroy(t->right);
    free(t);
}

int main(void) {
    int64_t result = 0;
    int64_t i = 0;
    while (i < 1200) {
        Tree *tree = make(13);
        result += check(tree);
        destroy(tree);
        i += 1;
    }
    printf("%lld\n", (long long)result);
    return 0;
}
