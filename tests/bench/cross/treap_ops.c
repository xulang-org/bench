#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int64_t l;
    int64_t r;
} Pair;

typedef struct {
    int64_t *key;
    int64_t *pri;
    int64_t *left;
    int64_t *right;
    int64_t len;
    int64_t cap;
    int64_t free_head;
    int64_t root;
    int64_t size;
} Treap;

static void treap_init(Treap *t) {
    t->len = 0;
    t->cap = 32768;
    t->key = (int64_t *)malloc((size_t)t->cap * sizeof(int64_t));
    t->pri = (int64_t *)malloc((size_t)t->cap * sizeof(int64_t));
    t->left = (int64_t *)malloc((size_t)t->cap * sizeof(int64_t));
    t->right = (int64_t *)malloc((size_t)t->cap * sizeof(int64_t));
    t->free_head = -1;
    t->root = -1;
    t->size = 0;
}

static void treap_free(Treap *t) {
    free(t->key);
    free(t->pri);
    free(t->left);
    free(t->right);
}

static int64_t alloc_node(Treap *t, int64_t k, int64_t p) {
    if (t->free_head != -1) {
        int64_t idx = t->free_head;
        t->free_head = t->left[idx];
        t->key[idx] = k;
        t->pri[idx] = p;
        t->left[idx] = -1;
        t->right[idx] = -1;
        return idx;
    }
    if (t->len == t->cap) {
        t->cap *= 2;
        t->key = (int64_t *)realloc(t->key, (size_t)t->cap * sizeof(int64_t));
        t->pri = (int64_t *)realloc(t->pri, (size_t)t->cap * sizeof(int64_t));
        t->left = (int64_t *)realloc(t->left, (size_t)t->cap * sizeof(int64_t));
        t->right = (int64_t *)realloc(t->right, (size_t)t->cap * sizeof(int64_t));
    }
    int64_t idx = t->len++;
    t->key[idx] = k;
    t->pri[idx] = p;
    t->left[idx] = -1;
    t->right[idx] = -1;
    return idx;
}

static void free_node(Treap *t, int64_t idx) {
    t->left[idx] = t->free_head;
    t->right[idx] = -1;
    t->free_head = idx;
}

static Pair split(Treap *t, int64_t u, int64_t k) {
    if (u == -1) {
        Pair p = {-1, -1};
        return p;
    }
    if (t->key[u] < k) {
        Pair p = split(t, t->right[u], k);
        t->right[u] = p.l;
        Pair res = {u, p.r};
        return res;
    }
    Pair p = split(t, t->left[u], k);
    t->left[u] = p.r;
    Pair res = {p.l, u};
    return res;
}

static int64_t merge(Treap *t, int64_t a, int64_t b) {
    if (a == -1) return b;
    if (b == -1) return a;
    if (t->pri[a] > t->pri[b]) {
        t->right[a] = merge(t, t->right[a], b);
        return a;
    }
    t->left[b] = merge(t, a, t->left[b]);
    return b;
}

static int contains(const Treap *t, int64_t k) {
    int64_t u = t->root;
    while (u != -1) {
        int64_t ku = t->key[u];
        if (k == ku) return 1;
        u = (k < ku) ? t->left[u] : t->right[u];
    }
    return 0;
}

static void insert(Treap *t, int64_t k, int64_t p) {
    if (contains(t, k)) return;
    Pair sp = split(t, t->root, k);
    int64_t n = alloc_node(t, k, p);
    t->root = merge(t, merge(t, sp.l, n), sp.r);
    t->size += 1;
}

static void erase(Treap *t, int64_t k) {
    Pair sp1 = split(t, t->root, k);
    Pair sp2 = split(t, sp1.r, k + 1);
    if (sp2.l != -1) {
        free_node(t, sp2.l);
        t->size -= 1;
    }
    t->root = merge(t, sp1.l, sp2.r);
}

int main(void) {
    Treap tr;
    treap_init(&tr);
    int64_t rng = 123456789;
    int64_t hits = 0;
    int64_t ck = 0;
    for (int64_t step = 0; step < 120000; step++) {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        int64_t op = rng % 10;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        int64_t k = rng % 40000;
        if (op < 4) {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            insert(&tr, k, rng);
        } else if (op < 6) {
            erase(&tr, k);
        } else {
            if (contains(&tr, k)) {
                hits += 1;
                ck = (ck * 131 + k + 1) % 1000000007;
            }
        }
    }
    printf("%" PRId64 "\n%" PRId64 "\n%" PRId64 "\n", hits, ck, tr.size);
    treap_free(&tr);
    return 0;
}
