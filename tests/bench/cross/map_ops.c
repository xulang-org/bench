#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if defined(_MSC_VER)
#define NOINLINE __declspec(noinline)
#elif defined(__GNUC__) || defined(__clang__)
#define NOINLINE __attribute__((noinline))
#else
#define NOINLINE
#endif

typedef struct {
    int64_t *keys;
    int64_t *vals;
    uint8_t *used;
    int64_t n;
    int64_t cap;
} Map;

static inline uint64_t splitmix64(uint64_t x) {
    x ^= x >> 30;
    x *= 0xbf58476d1ce4e5b9ULL;
    x ^= x >> 27;
    x *= 0x94d049bb133111ebULL;
    x ^= x >> 31;
    return x;
}

static uint64_t mix(int64_t k, int64_t cap) {
    return splitmix64((uint64_t)k) & ((uint64_t)cap - 1);
}

static void map_reinsert(Map *m, int64_t k, int64_t v) {
    uint64_t i = mix(k, m->cap);
    uint64_t mask = (uint64_t)m->cap - 1;
    while (m->used[i]) {
        i = (i + 1) & mask;
    }
    m->used[i] = 1;
    m->keys[i] = k;
    m->vals[i] = v;
}

static void map_grow(Map *m) {
    int64_t ocap = m->cap;
    int64_t *okeys = m->keys;
    int64_t *ovals = m->vals;
    uint8_t *oused = m->used;
    m->cap *= 2;
    m->keys = (int64_t *)calloc((size_t)m->cap, sizeof(int64_t));
    m->vals = (int64_t *)calloc((size_t)m->cap, sizeof(int64_t));
    m->used = (uint8_t *)calloc((size_t)m->cap, 1);
    if (!m->keys || !m->vals || !m->used) {
        exit(1);
    }
    int64_t j = 0;
    while (j < ocap) {
        if (oused[j]) {
            map_reinsert(m, okeys[j], ovals[j]);
        }
        j += 1;
    }
    free(okeys);
    free(ovals);
    free(oused);
}

NOINLINE static void map_put(Map *m, int64_t k, int64_t v) {
    if ((m->n + 1) * 2 >= m->cap) {
        map_grow(m);
    }
    uint64_t i = mix(k, m->cap);
    uint64_t mask = (uint64_t)m->cap - 1;
    while (m->used[i]) {
        if (m->keys[i] == k) {
            m->vals[i] = v;
            return;
        }
        i = (i + 1) & mask;
    }
    m->used[i] = 1;
    m->keys[i] = k;
    m->vals[i] = v;
    m->n += 1;
}

NOINLINE static int64_t map_get(Map *m, int64_t k) {
    uint64_t i = mix(k, m->cap);
    uint64_t mask = (uint64_t)m->cap - 1;
    while (m->used[i]) {
        if (m->keys[i] == k) {
            return m->vals[i];
        }
        i = (i + 1) & mask;
    }
    return 0;
}

int main(void) {
    Map m;
    m.cap = 16;
    m.n = 0;
    m.keys = (int64_t *)calloc(16, sizeof(int64_t));
    m.vals = (int64_t *)calloc(16, sizeof(int64_t));
    m.used = (uint8_t *)calloc(16, 1);
    if (!m.keys || !m.vals || !m.used) {
        return 1;
    }
    int64_t i = 0;
    while (i < 200000) {
        map_put(&m, i, 1);
        i += 1;
    }
    int64_t s = 0;
    i = 0;
    while (i < 200000) {
        s += map_get(&m, i) + i;
        i += 1;
    }
    printf("%lld\n", (long long)s);
    free(m.keys);
    free(m.vals);
    free(m.used);
    return 0;
}
