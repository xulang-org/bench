#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

typedef struct {
    int64_t *data;
    size_t len;
    size_t cap;
} MinHeap;

static void heap_init(MinHeap *h) {
    h->cap = 16;
    h->len = 0;
    h->data = (int64_t *)malloc(h->cap * sizeof(int64_t));
}

static void heap_push(MinHeap *h, int64_t val) {
    if (h->len >= h->cap) {
        h->cap *= 2;
        h->data = (int64_t *)realloc(h->data, h->cap * sizeof(int64_t));
    }
    size_t j = h->len++;
    h->data[j] = val;
    while (j > 0) {
        size_t i = (j - 1) >> 1;
        if (h->data[j] >= h->data[i]) break;
        int64_t tmp = h->data[j];
        h->data[j] = h->data[i];
        h->data[i] = tmp;
        j = i;
    }
}

static int64_t heap_pop(MinHeap *h) {
    int64_t out = h->data[0];
    h->len--;
    if (h->len > 0) {
        h->data[0] = h->data[h->len];
        size_t root = 0;
        size_t n = h->len;
        while (1) {
            size_t child = root * 2 + 1;
            if (child >= n) break;
            if (child + 1 < n && h->data[child + 1] < h->data[child]) {
                child++;
            }
            if (h->data[child] < h->data[root]) {
                int64_t tmp = h->data[root];
                h->data[root] = h->data[child];
                h->data[child] = tmp;
                root = child;
            } else {
                break;
            }
        }
    }
    return out;
}

int main(void) {
    MinHeap h;
    heap_init(&h);
    int64_t seed = 123456789;
    int64_t checksum = 0;

    for (int i = 0; i < 200000; i++) {
        seed = (seed * 1664525 + 1013904223) % 2147483647;
        heap_push(&h, seed);
    }

    for (int i = 0; i < 100000; i++) {
        int64_t v = heap_pop(&h);
        checksum = (checksum * 31 + v) % 1000000007;
    }

    for (int i = 0; i < 100000; i++) {
        seed = (seed * 1664525 + 1013904223) % 2147483647;
        heap_push(&h, seed);
    }

    while (h.len > 0) {
        int64_t v = heap_pop(&h);
        checksum = (checksum * 31 + v) % 1000000007;
    }

    printf("%lld\n", (long long)checksum);
    free(h.data);
    return 0;
}
