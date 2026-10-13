#include <stdio.h>
#include <stdint.h>

static inline uint32_t rotl32(uint32_t v, int c) {
    return (v << c) | (v >> (32 - c));
}

static inline void qr(uint32_t *s, int a, int b, int c, int d) {
    s[a] += s[b]; s[d] = rotl32(s[d] ^ s[a], 16);
    s[c] += s[d]; s[b] = rotl32(s[b] ^ s[c], 12);
    s[a] += s[b]; s[d] = rotl32(s[d] ^ s[a], 8);
    s[c] += s[d]; s[b] = rotl32(s[b] ^ s[c], 7);
}

int main(void) {
    uint32_t s[16];
    uint32_t key[8];
    for (int i = 0; i < 8; i++) {
        key[i] = (uint32_t)(i * 16843009LL);
    }
    uint32_t nonce0 = 305419896;
    uint32_t nonce1 = 2596069104U;
    uint32_t nonce2 = 267246505;

    int rounds = 30000;
    uint32_t total_sum = 0;
    for (int block = 0; block < rounds; block++) {
        s[0] = 1634760805;
        s[1] = 857760878;
        s[2] = 2036477234;
        s[3] = 1797285236;
        for (int k = 0; k < 8; k++) {
            s[4 + k] = key[k] + (uint32_t)block;
        }
        s[12] = (uint32_t)block;
        s[13] = nonce0;
        s[14] = nonce1;
        s[15] = nonce2;

        for (int r = 0; r < 10; r++) {
            qr(s, 0, 4, 8, 12);
            qr(s, 1, 5, 9, 13);
            qr(s, 2, 6, 10, 14);
            qr(s, 3, 7, 11, 15);
            qr(s, 0, 5, 10, 15);
            qr(s, 1, 6, 11, 12);
            qr(s, 2, 7, 8, 13);
            qr(s, 3, 4, 9, 14);
        }
        total_sum += s[0] + s[5] + s[10] + s[15];
    }
    printf("%u\n", total_sum);
    return 0;
}
