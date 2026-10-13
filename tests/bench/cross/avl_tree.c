#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

typedef struct {
    int64_t *keys;
    int64_t *vals;
    int *heights;
    int *lefts;
    int *rights;
    int count;
    int root;
} AVL;

static inline int h(AVL *t, int idx) {
    return idx == -1 ? 0 : t->heights[idx];
}

static inline void upd(AVL *t, int idx) {
    int hl = h(t, t->lefts[idx]);
    int hr = h(t, t->rights[idx]);
    t->heights[idx] = 1 + (hl > hr ? hl : hr);
}

static inline int bf(AVL *t, int idx) {
    return h(t, t->lefts[idx]) - h(t, t->rights[idx]);
}

static int rot_r(AVL *t, int y) {
    int x = t->lefts[y];
    int t2 = t->rights[x];
    t->rights[x] = y;
    t->lefts[y] = t2;
    upd(t, y);
    upd(t, x);
    return x;
}

static int rot_l(AVL *t, int x) {
    int y = t->rights[x];
    int t2 = t->lefts[y];
    t->lefts[y] = x;
    t->rights[x] = t2;
    upd(t, x);
    upd(t, y);
    return y;
}

static int insert(AVL *t, int idx, int64_t key, int64_t val) {
    if (idx == -1) {
        int nid = t->count++;
        t->keys[nid] = key;
        t->vals[nid] = val;
        t->heights[nid] = 1;
        t->lefts[nid] = -1;
        t->rights[nid] = -1;
        return nid;
    }
    if (key < t->keys[idx]) {
        t->lefts[idx] = insert(t, t->lefts[idx], key, val);
    } else if (key > t->keys[idx]) {
        t->rights[idx] = insert(t, t->rights[idx], key, val);
    } else {
        t->vals[idx] = val;
        return idx;
    }
    upd(t, idx);
    int b = bf(t, idx);
    if (b > 1 && key < t->keys[t->lefts[idx]]) {
        return rot_r(t, idx);
    }
    if (b < -1 && key > t->keys[t->rights[idx]]) {
        return rot_l(t, idx);
    }
    if (b > 1 && key > t->keys[t->lefts[idx]]) {
        t->lefts[idx] = rot_l(t, t->lefts[idx]);
        return rot_r(t, idx);
    }
    if (b < -1 && key < t->keys[t->rights[idx]]) {
        t->rights[idx] = rot_r(t, t->rights[idx]);
        return rot_l(t, idx);
    }
    return idx;
}

static int64_t search(AVL *t, int64_t key) {
    int cur = t->root;
    while (cur != -1) {
        int64_t k = t->keys[cur];
        if (key == k) return t->vals[cur];
        if (key < k) cur = t->lefts[cur];
        else cur = t->rights[cur];
    }
    return 0;
}

int main(void) {
    int cap = 100000;
    AVL t;
    t.keys = malloc(sizeof(int64_t) * cap);
    t.vals = malloc(sizeof(int64_t) * cap);
    t.heights = malloc(sizeof(int) * cap);
    t.lefts = malloc(sizeof(int) * cap);
    t.rights = malloc(sizeof(int) * cap);
    t.count = 0;
    t.root = -1;

    int64_t seed = 123456789;
    for (int i = 0; i < 80000; i++) {
        seed = (seed * 1103515245 + 12345) & 0x7fffffff;
        int64_t k = seed % 200000;
        int64_t v = (i * 3 + 7) & 0x7fffffff;
        t.root = insert(&t, t.root, k, v);
    }

    int64_t checksum = 0;
    for (int i = 0; i < 300000; i++) {
        seed = (seed * 1103515245 + 12345) & 0x7fffffff;
        int64_t k = seed % 200000;
        int64_t val = search(&t, k);
        checksum = (checksum * 31 + val) % 1000000007;
    }
    printf("%lld\n", checksum);
    return 0;
}
