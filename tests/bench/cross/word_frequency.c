// Osprey (MIT): benchmarks/cases/wordfreq; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// String-keyed frequency map, 200000 tokens, deterministic seed=1.
// Every token performs a map lookup followed by an update (not an indexed counter).
// Eight immutable ASCII keys; weighted final counts; see tests/bench/osprey/README.md.

#include <stdint.h>
#include <stdio.h>
#include <string.h>

// Generic string-keyed open addressing (FNV-1a, linear probing), 16 slots.
// Eight distinct keys fit at <=50% load; immutable key bytes are borrowed.
typedef struct { const char *keys[16]; int64_t values[16]; } Map;

static uint64_t slot(const Map *m, const char *key) {
    uint64_t h = UINT64_C(14695981039346656037);
    const unsigned char *p = (const unsigned char *)key;
    while (*p) { h = (h ^ *p) * UINT64_C(1099511628211); p += 1; }
    h &= 15;
    while (m->keys[h] && strcmp(m->keys[h], key) != 0) { h = (h + 1) & 15; }
    return h;
}

static int64_t get(const Map *m, const char *key) {
    uint64_t i = slot(m, key);
    return m->keys[i] ? m->values[i] : 0;
}

static void put(Map *m, const char *key, int64_t value) {
    uint64_t i = slot(m, key);
    m->keys[i] = key;
    m->values[i] = value;
}

static int64_t hash_at(int64_t seed, int64_t i) {
    return (((seed + i) * 16807) % 2147483647 * 16807) % 2147483647;
}

static const char *word(int64_t k) {
    if (k == 0) { return "the"; }
    if (k == 1) { return "quick"; }
    if (k == 2) { return "brown"; }
    if (k == 3) { return "fox"; }
    if (k == 4) { return "jumps"; }
    if (k == 5) { return "over"; }
    if (k == 6) { return "lazy"; }
    return "dog";
}

int main(void) {
    Map counts = {{0}, {0}};
    int64_t i = 0;
    while (i < 200000) {
        const char *w = word(hash_at(1, i) % 8);
        int64_t count = get(&counts, w);
        put(&counts, w, count + 1);
        i += 1;
    }
    int64_t result = 0;
    i = 0;
    while (i < 8) {
        result += (i + 1) * get(&counts, word(i));
        i += 1;
    }
    printf("%lld\n", (long long)result);
    return 0;
}
