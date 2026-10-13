#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

static const uint32_t K[64] = {
    0x428a2f98u, 0x71374491u, 0xb5c0fbcfu, 0xe9b5dba5u, 0x3956c25bu, 0x59f111f1u, 0x923f82a4u, 0xab1c5ed5u,
    0xd807aa98u, 0x12835b01u, 0x243185beu, 0x550c7dc3u, 0x72be5d74u, 0x80deb1feu, 0x9bdc06a7u, 0xc19bf174u,
    0xe49b69c1u, 0xefbe4786u, 0x0fc19dc6u, 0x240ca1ccu, 0x2de92c6fu, 0x4a7484aau, 0x5cb0a9dcu, 0x76f988dau,
    0x983e5152u, 0xa831c66du, 0xb00327c8u, 0xbf597fc7u, 0xc6e00bf3u, 0xd5a79147u, 0x06ca6351u, 0x14292967u,
    0x27b70a85u, 0x2e1b2138u, 0x4d2c6dfcu, 0x53380d13u, 0x650a7354u, 0x766a0abbu, 0x81c2c92eu, 0x92722c85u,
    0xa2bfe8a1u, 0xa81a664bu, 0xc24b8b70u, 0xc76c51a3u, 0xd192e819u, 0xd6990624u, 0xf40e3585u, 0x106aa070u,
    0x19a4c116u, 0x1e376c08u, 0x2748774cu, 0x34b0bcb5u, 0x391c0cb3u, 0x4ed8aa4au, 0x5b9cca4fu, 0x682e6ff3u,
    0x748f82eeu, 0x78a5636fu, 0x84c87814u, 0x8cc70208u, 0x90befffau, 0xa4506cebu, 0xbef9a3f7u, 0xc67178f2u,
};

static uint32_t rotr(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }

static void sha256_transform(uint32_t st[8], const uint8_t blk[64]) {
    uint32_t w[64];
    int i;
    for (i = 0; i < 16; i++) {
        w[i] = ((uint32_t)blk[i * 4] << 24) | ((uint32_t)blk[i * 4 + 1] << 16) |
               ((uint32_t)blk[i * 4 + 2] << 8) | (uint32_t)blk[i * 4 + 3];
    }
    for (i = 16; i < 64; i++) {
        uint32_t s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >> 3);
        uint32_t s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >> 10);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    uint32_t a = st[0], b = st[1], c = st[2], d = st[3];
    uint32_t e = st[4], f = st[5], g = st[6], h = st[7];
    for (i = 0; i < 64; i++) {
        uint32_t S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
        uint32_t ch = (e & f) ^ ((~e) & g);
        uint32_t t1 = h + S1 + ch + K[i] + w[i];
        uint32_t S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
        uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
        uint32_t t2 = S0 + maj;
        h = g;
        g = f;
        f = e;
        e = d + t1;
        d = c;
        c = b;
        b = a;
        a = t1 + t2;
    }
    st[0] += a;
    st[1] += b;
    st[2] += c;
    st[3] += d;
    st[4] += e;
    st[5] += f;
    st[6] += g;
    st[7] += h;
}

static void sha256(const uint8_t *msg, size_t len, uint8_t out[32]) {
    uint32_t st[8] = {0x6a09e667u, 0xbb67ae85u, 0x3c6ef372u, 0xa54ff53au,
                      0x510e527fu, 0x9b05688cu, 0x1f83d9abu, 0x5be0cd19u};
    uint8_t blk[64];
    size_t i = 0;
    while (i + 64 <= len) {
        sha256_transform(st, msg + i);
        i += 64;
    }
    size_t rem = len - i;
    memset(blk, 0, 64);
    memcpy(blk, msg + i, rem);
    blk[rem] = 0x80;
    uint64_t bits = (uint64_t)len * 8;
    if (rem >= 56) {
        sha256_transform(st, blk);
        memset(blk, 0, 64);
    }
    for (int j = 0; j < 8; j++) {
        blk[63 - j] = (uint8_t)(bits >> (8 * j));
    }
    sha256_transform(st, blk);
    for (int j = 0; j < 8; j++) {
        out[j * 4] = (uint8_t)(st[j] >> 24);
        out[j * 4 + 1] = (uint8_t)(st[j] >> 16);
        out[j * 4 + 2] = (uint8_t)(st[j] >> 8);
        out[j * 4 + 3] = (uint8_t)st[j];
    }
}

static void hex32(const uint8_t d[32], char out[65]) {
    static const char *h = "0123456789abcdef";
    for (int i = 0; i < 32; i++) {
        out[i * 2] = h[d[i] >> 4];
        out[i * 2 + 1] = h[d[i] & 15];
    }
    out[64] = 0;
}

int main(void) {
    const char *chunk = "The quick brown fox jumps over the lazy dog. 0123456789.";
    size_t clen = strlen(chunk);
    size_t blen = clen * 1024;
    char *body = (char *)malloc(blen);
    if (!body) {
        return 1;
    }
    for (int i = 0; i < 1024; i++) {
        memcpy(body + (size_t)i * clen, chunk, clen);
    }
    uint8_t dig[32];
    char hex[65];
    sha256((const uint8_t *)body, blen, dig);
    hex32(dig, hex);
    size_t cat_len = 64 + blen;
    char *cat = (char *)malloc(cat_len);
    if (!cat) {
        return 1;
    }
    memcpy(cat + 64, body, blen);
    for (int r = 0; r < 4; r++) {
        memcpy(cat, hex, 64);
        sha256((const uint8_t *)cat, cat_len, dig);
        hex32(dig, hex);
    }
    printf("%s\n", hex);
    free(cat);
    free(body);
    return 0;
}
