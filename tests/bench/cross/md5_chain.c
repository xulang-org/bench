#include <stdio.h>
#include <string.h>
#include <stdint.h>

static void md5_step(uint32_t state[4], const uint8_t block[64]) {
    uint32_t a = state[0], b = state[1], c = state[2], d = state[3];
    uint32_t x[16];
    for (int i = 0; i < 16; i++) {
        x[i] = (uint32_t)block[i*4] | ((uint32_t)block[i*4+1] << 8) |
               ((uint32_t)block[i*4+2] << 16) | ((uint32_t)block[i*4+3] << 24);
    }

    #define ROTL(x, n) (((x) << (n)) | ((x) >> (32 - (n))))
    #define FF(a, b, c, d, k, s, t) { (a) += (((b) & (c)) | ((~b) & (d))) + x[k] + (t); (a) = ROTL(a, s) + (b); }
    #define GG(a, b, c, d, k, s, t) { (a) += (((b) & (d)) | ((c) & (~d))) + x[k] + (t); (a) = ROTL(a, s) + (b); }
    #define HH(a, b, c, d, k, s, t) { (a) += ((b) ^ (c) ^ (d)) + x[k] + (t); (a) = ROTL(a, s) + (b); }
    #define II(a, b, c, d, k, s, t) { (a) += ((c) ^ ((b) | (~d))) + x[k] + (t); (a) = ROTL(a, s) + (b); }

    FF(a, b, c, d,  0,  7, 0xd76aa478); FF(d, a, b, c,  1, 12, 0xe8c7b756);
    FF(c, d, a, b,  2, 17, 0x242070db); FF(b, c, d, a,  3, 22, 0xc1bdceee);
    FF(a, b, c, d,  4,  7, 0xf57c0faf); FF(d, a, b, c,  5, 12, 0x4787c62a);
    FF(c, d, a, b,  6, 17, 0xa8304613); FF(b, c, d, a,  7, 22, 0xfd469501);
    FF(a, b, c, d,  8,  7, 0x698098d8); FF(d, a, b, c,  9, 12, 0x8b44f7af);
    FF(c, d, a, b, 10, 17, 0xffff5bb1); FF(b, c, d, a, 11, 22, 0x895cd7be);
    FF(a, b, c, d, 12,  7, 0x6b901122); FF(d, a, b, c, 13, 12, 0xfd987193);
    FF(c, d, a, b, 14, 17, 0xa679438e); FF(b, c, d, a, 15, 22, 0x49b40821);

    GG(a, b, c, d,  1,  5, 0xf61e2562); GG(d, a, b, c,  6,  9, 0xc040b340);
    GG(c, d, a, b, 11, 14, 0x265e5a51); GG(b, c, d, a,  0, 20, 0xe9b6c7aa);
    GG(a, b, c, d,  5,  5, 0xd62f105d); GG(d, a, b, c, 10,  9, 0x02441453);
    GG(c, d, a, b, 15, 14, 0xd8a1e681); GG(b, c, d, a,  4, 20, 0xe7d3fbc8);
    GG(a, b, c, d,  9,  5, 0x21e1cde6); GG(d, a, b, c, 14,  9, 0xc33707d6);
    GG(c, d, a, b,  3, 14, 0xf4d50d87); GG(b, c, d, a,  8, 20, 0x455a14ed);
    GG(a, b, c, d, 13,  5, 0xa9e3e905); GG(d, a, b, c,  2,  9, 0xfcefa3f8);
    GG(c, d, a, b,  7, 14, 0x676f02d9); GG(b, c, d, a, 12, 20, 0x8d2a4c8a);

    HH(a, b, c, d,  5,  4, 0xfffa3942); HH(d, a, b, c,  8, 11, 0x8771f681);
    HH(c, d, a, b, 11, 16, 0x6d9d6122); HH(b, c, d, a, 14, 23, 0xfde5380c);
    HH(a, b, c, d,  1,  4, 0xa4beea44); HH(d, a, b, c,  4, 11, 0x4bdecfa9);
    HH(c, d, a, b,  7, 16, 0xf6bb4b60); HH(b, c, d, a, 10, 23, 0xbebfbc70);
    HH(a, b, c, d, 13,  4, 0x289b7ec6); HH(d, a, b, c,  0, 11, 0xeaa127fa);
    HH(c, d, a, b,  3, 16, 0xd4ef3085); HH(b, c, d, a,  6, 23, 0x04881d05);
    HH(a, b, c, d,  9,  4, 0xd9d4d039); HH(d, a, b, c, 12, 11, 0xe6db99e5);
    HH(c, d, a, b, 15, 16, 0x1fa27cf8); HH(b, c, d, a,  2, 23, 0xc4ac5665);

    II(a, b, c, d,  0,  6, 0xf4292244); II(d, a, b, c,  7, 10, 0x432aff97);
    II(c, d, a, b, 14, 15, 0xab9423a7); II(b, c, d, a,  5, 21, 0xfc93a039);
    II(a, b, c, d, 12,  6, 0x655b59c3); II(d, a, b, c,  3, 10, 0x8f0ccc92);
    II(c, d, a, b, 10, 15, 0xffeff47d); II(b, c, d, a,  1, 21, 0x85845dd1);
    II(a, b, c, d,  8,  6, 0x6fa87e4f); II(d, a, b, c, 15, 10, 0xfe2ce6e0);
    II(c, d, a, b,  6, 15, 0xa3014314); II(b, c, d, a, 13, 21, 0x4e0811a1);
    II(a, b, c, d,  4,  6, 0xf7537e82); II(d, a, b, c, 11, 10, 0xbd3af235);
    II(c, d, a, b,  2, 15, 0x2ad7d2bb); II(b, c, d, a,  9, 21, 0xeb86d391);

    state[0] += a; state[1] += b; state[2] += c; state[3] += d;
}

static void md5_sum(const char *msg, size_t len, char *out_hex) {
    uint32_t state[4] = {0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476};
    uint64_t bit_len = (uint64_t)len * 8;
    size_t padded_len = ((len + 8) / 64 + 1) * 64;
    uint8_t buf[128] = {0};
    memcpy(buf, msg, len);
    buf[len] = 0x80;
    memcpy(buf + padded_len - 8, &bit_len, 8);

    for (size_t i = 0; i < padded_len; i += 64) {
        md5_step(state, buf + i);
    }

    static const char hex_digits[] = "0123456789abcdef";
    for (int i = 0; i < 4; i++) {
        uint32_t v = state[i];
        out_hex[i*8+0] = hex_digits[(v >> 4) & 0xF];
        out_hex[i*8+1] = hex_digits[v & 0xF];
        out_hex[i*8+2] = hex_digits[(v >> 12) & 0xF];
        out_hex[i*8+3] = hex_digits[(v >> 8) & 0xF];
        out_hex[i*8+4] = hex_digits[(v >> 20) & 0xF];
        out_hex[i*8+5] = hex_digits[(v >> 16) & 0xF];
        out_hex[i*8+6] = hex_digits[(v >> 28) & 0xF];
        out_hex[i*8+7] = hex_digits[(v >> 24) & 0xF];
    }
    out_hex[32] = '\0';
}

int main(void) {
    char h[64] = "The quick brown fox jumps over the lazy dog";
    for (int i = 0; i < 100000; i++) {
        md5_sum(h, strlen(h), h);
    }
    printf("%s\n", h);
    return 0;
}
