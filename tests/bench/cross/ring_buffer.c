#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

typedef struct {
    int64_t *buf;
    size_t cap;
    size_t head;
    size_t tail;
    size_t count;
    size_t mask;
} Deque;

static void deque_init(Deque *d) {
    d->cap = 16;
    d->mask = 15;
    d->buf = (int64_t *)calloc(d->cap, sizeof(int64_t));
    d->head = 0;
    d->tail = 0;
    d->count = 0;
}

static void deque_grow(Deque *d) {
    size_t old_cap = d->cap;
    size_t old_mask = d->mask;
    size_t new_cap = old_cap * 2;
    int64_t *new_buf = (int64_t *)calloc(new_cap, sizeof(int64_t));
    for (size_t j = 0; j < d->count; j++) {
        new_buf[j] = d->buf[(d->head + j) & old_mask];
    }
    free(d->buf);
    d->buf = new_buf;
    d->cap = new_cap;
    d->mask = new_cap - 1;
    d->head = 0;
    d->tail = d->count;
}

static void deque_push_back(Deque *d, int64_t val) {
    if (d->count == d->cap) {
        deque_grow(d);
    }
    d->buf[d->tail] = val;
    d->tail = (d->tail + 1) & d->mask;
    d->count++;
}

static void deque_push_front(Deque *d, int64_t val) {
    if (d->count == d->cap) {
        deque_grow(d);
    }
    d->head = (d->head - 1) & d->mask;
    d->buf[d->head] = val;
    d->count++;
}

static int64_t deque_pop_front(Deque *d) {
    if (d->count == 0) return 0;
    int64_t val = d->buf[d->head];
    d->head = (d->head + 1) & d->mask;
    d->count--;
    return val;
}

static int64_t deque_pop_back(Deque *d) {
    if (d->count == 0) return 0;
    d->tail = (d->tail - 1) & d->mask;
    int64_t val = d->buf[d->tail];
    d->count--;
    return val;
}

int main(void) {
    Deque q;
    deque_init(&q);
    int64_t seed = 123456789;
    int64_t checksum = 0;

    for (int i = 0; i < 5000000; i++) {
        seed = (seed * 1664525 + 1013904223) % 2147483647;
        int64_t op = seed % 4;
        if (op == 0) {
            deque_push_back(&q, seed);
        } else if (op == 1) {
            deque_push_front(&q, seed);
        } else if (op == 2) {
            int64_t v = deque_pop_front(&q);
            checksum = (checksum * 33 + v) % 1000000007;
        } else {
            int64_t v = deque_pop_back(&q);
            checksum = (checksum * 33 + v) % 1000000007;
        }
    }

    while (q.count > 0) {
        int64_t v = deque_pop_front(&q);
        checksum = (checksum * 33 + v) % 1000000007;
    }

    printf("%lld\n", (long long)checksum);
    free(q.buf);
    return 0;
}
