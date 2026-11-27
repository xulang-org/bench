#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MOD_V 1000000007LL

typedef struct {
    int64_t *is_leaf;
    int64_t *nkeys;
    int64_t *next_leaf;
    int64_t *keys;
    int64_t *vals;
    int64_t *children;
    int len;
    int cap;
    int path_node[16];
    int path_idx[16];
    int root;
} BPlusTree;

static void ensure_node_cap(BPlusTree *t) {
    if (t->len < t->cap) {
        return;
    }
    int ncap = t->cap * 2;
    t->is_leaf = (int64_t *)realloc(t->is_leaf, (size_t)ncap * sizeof(int64_t));
    t->nkeys = (int64_t *)realloc(t->nkeys, (size_t)ncap * sizeof(int64_t));
    t->next_leaf = (int64_t *)realloc(t->next_leaf, (size_t)ncap * sizeof(int64_t));
    t->keys = (int64_t *)realloc(t->keys, (size_t)ncap * 32 * sizeof(int64_t));
    t->vals = (int64_t *)realloc(t->vals, (size_t)ncap * 32 * sizeof(int64_t));
    t->children = (int64_t *)realloc(t->children, (size_t)ncap * 33 * sizeof(int64_t));
    t->cap = ncap;
}

static int alloc_node(BPlusTree *t, int64_t leaf) {
    ensure_node_cap(t);
    int u = t->len++;
    t->is_leaf[u] = leaf;
    t->nkeys[u] = 0;
    t->next_leaf[u] = -1;
    int base = u * 32;
    int cbase = u * 33;
    for (int j = 0; j < 32; j++) {
        t->keys[base + j] = 0;
        t->vals[base + j] = 0;
    }
    for (int c = 0; c < 33; c++) {
        t->children[cbase + c] = -1;
    }
    return u;
}

static void init_btree(BPlusTree *t) {
    t->cap = 256;
    t->len = 0;
    t->is_leaf = (int64_t *)malloc((size_t)t->cap * sizeof(int64_t));
    t->nkeys = (int64_t *)malloc((size_t)t->cap * sizeof(int64_t));
    t->next_leaf = (int64_t *)malloc((size_t)t->cap * sizeof(int64_t));
    t->keys = (int64_t *)malloc((size_t)t->cap * 32 * sizeof(int64_t));
    t->vals = (int64_t *)malloc((size_t)t->cap * 32 * sizeof(int64_t));
    t->children = (int64_t *)malloc((size_t)t->cap * 33 * sizeof(int64_t));
    t->root = alloc_node(t, 1);
}

static void free_btree(BPlusTree *t) {
    free(t->is_leaf);
    free(t->nkeys);
    free(t->next_leaf);
    free(t->keys);
    free(t->vals);
    free(t->children);
}

static int descend_leaf(const BPlusTree *t, int64_t k) {
    int u = t->root;
    while (t->is_leaf[u] == 0) {
        int base = u * 32;
        int lo = 0;
        int hi = (int)t->nkeys[u];
        while (lo < hi) {
            int mid = (lo + hi) >> 1;
            if (t->keys[base + mid] <= k) {
                lo = mid + 1;
            } else {
                hi = mid;
            }
        }
        u = (int)t->children[u * 33 + lo];
    }
    return u;
}

static void bt_insert(BPlusTree *t, int64_t k, int64_t v) {
    int u = t->root;
    int depth = 0;
    while (t->is_leaf[u] == 0) {
        int base = u * 32;
        int lo = 0;
        int hi = (int)t->nkeys[u];
        while (lo < hi) {
            int mid = (lo + hi) >> 1;
            if (t->keys[base + mid] <= k) {
                lo = mid + 1;
            } else {
                hi = mid;
            }
        }
        t->path_node[depth] = u;
        t->path_idx[depth] = lo;
        depth++;
        u = (int)t->children[u * 33 + lo];
    }

    int base = u * 32;
    int n = (int)t->nkeys[u];
    int lo = 0;
    int hi = n;
    while (lo < hi) {
        int mid = (lo + hi) >> 1;
        if (t->keys[base + mid] < k) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    if (lo < n && t->keys[base + lo] == k) {
        t->vals[base + lo] = v;
        return;
    }
    for (int j = n; j > lo; j--) {
        t->keys[base + j] = t->keys[base + j - 1];
        t->vals[base + j] = t->vals[base + j - 1];
    }
    t->keys[base + lo] = k;
    t->vals[base + lo] = v;
    n++;
    t->nkeys[u] = n;
    if (n < 32) {
        return;
    }

    int r = alloc_node(t, 1);
    base = u * 32;
    int rbase = r * 32;
    for (int j = 0; j < 16; j++) {
        t->keys[rbase + j] = t->keys[base + 16 + j];
        t->vals[rbase + j] = t->vals[base + 16 + j];
    }
    t->nkeys[u] = 16;
    t->nkeys[r] = 16;
    t->next_leaf[r] = t->next_leaf[u];
    t->next_leaf[u] = r;
    int64_t up_key = t->keys[rbase];
    int64_t up_right = r;

    for (int d = depth - 1; d >= 0; d--) {
        int p = t->path_node[d];
        int ins = t->path_idx[d];
        int pbase = p * 32;
        int pcbase = p * 33;
        int pn = (int)t->nkeys[p];
        for (int k_idx = pn; k_idx > ins; k_idx--) {
            t->keys[pbase + k_idx] = t->keys[pbase + k_idx - 1];
            t->children[pcbase + k_idx + 1] = t->children[pcbase + k_idx];
        }
        t->keys[pbase + ins] = up_key;
        t->children[pcbase + ins + 1] = up_right;
        pn++;
        t->nkeys[p] = pn;
        if (pn < 32) {
            return;
        }
        int nr = alloc_node(t, 0);
        pbase = p * 32;
        pcbase = p * 33;
        int nrbase = nr * 32;
        int nrcbase = nr * 33;
        int64_t mid_key = t->keys[pbase + 16];
        for (int m = 0; m < 15; m++) {
            t->keys[nrbase + m] = t->keys[pbase + 17 + m];
        }
        for (int c = 0; c < 16; c++) {
            t->children[nrcbase + c] = t->children[pcbase + 17 + c];
        }
        t->nkeys[p] = 16;
        t->nkeys[nr] = 15;
        up_key = mid_key;
        up_right = nr;
    }

    int new_root = alloc_node(t, 0);
    t->keys[new_root * 32] = up_key;
    t->children[new_root * 33] = t->root;
    t->children[new_root * 33 + 1] = up_right;
    t->nkeys[new_root] = 1;
    t->root = new_root;
}

static int64_t bt_lookup(const BPlusTree *t, int64_t k) {
    int u = descend_leaf(t, k);
    int base = u * 32;
    int n = (int)t->nkeys[u];
    int lo = 0;
    int hi = n;
    while (lo < hi) {
        int mid = (lo + hi) >> 1;
        if (t->keys[base + mid] < k) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    if (lo < n && t->keys[base + lo] == k) {
        return t->vals[base + lo];
    }
    return -1;
}

int main(void) {
    BPlusTree t;
    init_btree(&t);
    int64_t rng = 123456789LL;

    for (int64_t i = 0; i < 80000; i++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int64_t k = rng % 1000000LL;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int64_t v = (i * 17LL + (rng & 1023LL)) % 1000000LL;
        bt_insert(&t, k, v);
    }

    int64_t hits = 0;
    int64_t ck = 0;
    for (int q = 0; q < 120000; q++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int64_t k = rng % 1000000LL;
        int64_t v = bt_lookup(&t, k);
        if (v >= 0) {
            hits++;
            ck = (ck * 31LL + v) % MOD_V;
        }
    }

    int64_t rcnt = 0;
    for (int r = 0; r < 2000; r++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int64_t lo_k = rng % 999000LL;
        int64_t hi_k = lo_k + 1000LL;
        int u = descend_leaf(&t, lo_k);
        int base0 = u * 32;
        int n0 = (int)t.nkeys[u];
        int lo = 0;
        int hi = n0;
        while (lo < hi) {
            int mid = (lo + hi) >> 1;
            if (t.keys[base0 + mid] < lo_k) {
                lo = mid + 1;
            } else {
                hi = mid;
            }
        }
        int64_t cnt = 0;
        int64_t s = 0;
        int idx = lo;
        while (u != -1) {
            int base = u * 32;
            int n = (int)t.nkeys[u];
            int done = 0;
            for (int j = idx; j < n; j++) {
                if (t.keys[base + j] > hi_k) {
                    done = 1;
                    break;
                }
                cnt++;
                s = (s + t.vals[base + j]) % MOD_V;
            }
            if (done) {
                break;
            }
            u = (int)t.next_leaf[u];
            idx = 0;
        }
        rcnt += cnt;
        ck = (ck * 37LL + s + cnt) % MOD_V;
    }

    printf("%" PRId64 "\n%" PRId64 "\n", hits + rcnt, ck);
    free_btree(&t);
    return 0;
}
