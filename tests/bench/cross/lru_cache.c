#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

typedef struct {
    int64_t key;
    int64_t val;
    int32_t prev;
    int32_t next;
} Node;

typedef struct {
    Node *nodes;
    int32_t *table;
    int32_t head;
    int32_t tail;
    int32_t cap;
    int32_t count;
} LRU;

static void lru_init(LRU *l, int32_t cap, int32_t table_size) {
    l->nodes = (Node *)malloc(cap * sizeof(Node));
    for (int32_t i = 0; i < cap; i++) {
        l->nodes[i].key = -1;
        l->nodes[i].val = 0;
        l->nodes[i].prev = -1;
        l->nodes[i].next = -1;
    }
    l->table = (int32_t *)malloc(table_size * sizeof(int32_t));
    for (int32_t i = 0; i < table_size; i++) {
        l->table[i] = -1;
    }
    l->head = -1;
    l->tail = -1;
    l->cap = cap;
    l->count = 0;
}

static void lru_remove(LRU *l, int32_t idx) {
    int32_t p = l->nodes[idx].prev;
    int32_t n = l->nodes[idx].next;
    if (p >= 0) l->nodes[p].next = n;
    else l->head = n;
    if (n >= 0) l->nodes[n].prev = p;
    else l->tail = p;
}

static void lru_push_front(LRU *l, int32_t idx) {
    l->nodes[idx].prev = -1;
    l->nodes[idx].next = l->head;
    if (l->head >= 0) l->nodes[l->head].prev = idx;
    l->head = idx;
    if (l->tail < 0) l->tail = idx;
}

static int64_t lru_put(LRU *l, int64_t key, int64_t val) {
    int32_t old_idx = l->table[key];
    if (old_idx >= 0) {
        l->nodes[old_idx].val = val;
        lru_remove(l, old_idx);
        lru_push_front(l, old_idx);
        return val;
    }
    int32_t idx;
    if (l->count < l->cap) {
        idx = l->count++;
    } else {
        idx = l->tail;
        int64_t old_key = l->nodes[idx].key;
        l->table[old_key] = -1;
        lru_remove(l, idx);
    }
    l->nodes[idx].key = key;
    l->nodes[idx].val = val;
    l->table[key] = idx;
    lru_push_front(l, idx);
    return val;
}

static int64_t lru_get(LRU *l, int64_t key) {
    int32_t idx = l->table[key];
    if (idx < 0) return -1;
    lru_remove(l, idx);
    lru_push_front(l, idx);
    return l->nodes[idx].val;
}

int main(void) {
    LRU lru;
    lru_init(&lru, 1000, 3000);
    int64_t seed = 123456789;
    int64_t checksum = 0;

    for (int i = 0; i < 2500000; i++) {
        seed = (seed * 1664525 + 1013904223) % 2147483647;
        int64_t key = seed % 3000;
        int64_t val = seed % 1000000;
        if ((seed & 1) == 0) {
            int64_t res = lru_put(&lru, key, val);
            checksum = (checksum * 33 + res) % 1000000007;
        } else {
            int64_t res = lru_get(&lru, key);
            checksum = (checksum * 33 + res) % 1000000007;
        }
    }

    printf("%lld\n", (long long)checksum);
    free(lru.nodes);
    free(lru.table);
    return 0;
}
