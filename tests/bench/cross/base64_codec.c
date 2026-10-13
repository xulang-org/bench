#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

static const char b64_table[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

static int b64_val(char c) {
    if (c >= 'A' && c <= 'Z') return c - 'A';
    if (c >= 'a' && c <= 'z') return c - 'a' + 26;
    if (c >= '0' && c <= '9') return c - '0' + 52;
    if (c == '+') return 62;
    if (c == '/') return 63;
    return -1;
}

int main(void) {
    const char *base = "The quick brown fox jumps over the lazy dog 0123456789 ABCDEFGHIJKLMNOP";
    size_t base_len = strlen(base);
    size_t payload_len = base_len * 6; // 384
    char *payload = (char *)malloc(payload_len + 1);
    for (int i = 0; i < 6; i++) {
        memcpy(payload + i * base_len, base, base_len);
    }
    payload[payload_len] = '\0';

    size_t enc_len = (payload_len + 2) / 3 * 4; // 512
    char *enc = (char *)malloc(enc_len + 1);
    char *dec = (char *)malloc(payload_len + 1);

    int64_t total = 0;

    for (int i = 0; i < 15000; i++) {
        // Encode
        size_t di = 0;
        for (size_t si = 0; si < payload_len; si += 3) {
            uint32_t b0 = (uint8_t)payload[si];
            uint32_t b1 = (uint8_t)payload[si + 1];
            uint32_t b2 = (uint8_t)payload[si + 2];
            uint32_t triple = (b0 << 16) | (b1 << 8) | b2;
            enc[di++] = b64_table[(triple >> 18) & 0x3F];
            enc[di++] = b64_table[(triple >> 12) & 0x3F];
            enc[di++] = b64_table[(triple >> 6) & 0x3F];
            enc[di++] = b64_table[triple & 0x3F];
        }
        enc[di] = '\0';

        // Decode
        size_t out_i = 0;
        for (size_t si = 0; si < enc_len; si += 4) {
            int v0 = b64_val(enc[si]);
            int v1 = b64_val(enc[si + 1]);
            int v2 = b64_val(enc[si + 2]);
            int v3 = b64_val(enc[si + 3]);
            uint32_t triple = (v0 << 18) | (v1 << 12) | (v2 << 6) | v3;
            dec[out_i++] = (char)((triple >> 16) & 0xFF);
            dec[out_i++] = (char)((triple >> 8) & 0xFF);
            dec[out_i++] = (char)(triple & 0xFF);
        }
        dec[out_i] = '\0';

        total += (int64_t)enc_len + (int64_t)out_i;
        if (i == 0) {
            total += (uint8_t)dec[0] + (uint8_t)dec[out_i - 1];
        }
    }

    printf("%lld\n", (long long)total);

    free(payload);
    free(enc);
    free(dec);
    return 0;
}
