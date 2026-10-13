#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>

typedef struct {
    uint64_t *bits;
    uint64_t mask;
} BloomFilter;

static void bf_init(BloomFilter *bf, uint64_t num_bits) {
    bf->bits = (uint64_t *)calloc(num_bits / 64, sizeof(uint64_t));
    bf->mask = num_bits - 1;
}

static void bf_add(BloomFilter *bf, int64_t val) {
    int64_t h1 = (val * 1103515245 + 12345) & 2147483647;
    int64_t h2 = (val * 1664525 + 1013904223) & 2147483647;
    for (int i = 0; i < 4; i++) {
        uint64_t bit = (uint64_t)(h1 + i * h2) & bf->mask;
        bf->bits[bit >> 6] |= (1ULL << (bit & 63));
    }
}

static bool bf_contains(const BloomFilter *bf, int64_t val) {
    int64_t h1 = (val * 1103515245 + 12345) & 2147483647;
    int64_t h2 = (val * 1664525 + 1013904223) & 2147483647;
    for (int i = 0; i < 4; i++) {
        uint64_t bit = (uint64_t)(h1 + i * h2) & bf->mask;
        if ((bf->bits[bit >> 6] & (1ULL << (bit & 63))) == 0) {
            return false;
        }
    }
    return true;
}

int main(void) {
    BloomFilter bf;
    bf_init(&bf, 1048576);
    int64_t seed = 123456789;

    for (int i = 0; i < 200000; i++) {
        seed = (seed * 1664525 + 1013904223) % 2147483647;
        bf_add(&bf, seed);
    }

    int64_t checksum = 0;
    for (int i = 0; i < 2000000; i++) {
        seed = (seed * 1664525 + 1013904223) % 2147483647;
        if (bf_contains(&bf, seed)) {
            checksum = (checksum * 31 + seed) % 1000000007;
        }
    }

    printf("%lld\n", (long long)checksum);
    free(bf.bits);
    return 0;
}
