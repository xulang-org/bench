#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

static const char hex_digits[] = "0123456789abcdef";

static int hex_val(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

int main(void) {
    const char *base = "The quick brown fox jumps over the lazy dog 0123456789 ABCDEFGHIJKLMNOP";
    size_t base_len = strlen(base);
    size_t payload_len = base_len * 8;
    char *payload = (char *)malloc(payload_len + 1);
    for (int i = 0; i < 8; i++) {
        memcpy(payload + i * base_len, base, base_len);
    }
    payload[payload_len] = '\0';

    int64_t total = 0;
    char *enc = (char *)malloc(payload_len * 2 + 1);
    char *dec = (char *)malloc(payload_len + 1);

    for (int i = 0; i < 25000; i++) {
        for (size_t j = 0; j < payload_len; j++) {
            uint8_t c = (uint8_t)payload[j];
            enc[2 * j] = hex_digits[c >> 4];
            enc[2 * j + 1] = hex_digits[c & 0xF];
        }
        enc[payload_len * 2] = '\0';
        size_t enc_len = payload_len * 2;

        for (size_t j = 0; j < payload_len; j++) {
            int hi = hex_val(enc[2 * j]);
            int lo = hex_val(enc[2 * j + 1]);
            dec[j] = (char)((hi << 4) | lo);
        }
        dec[payload_len] = '\0';
        size_t dec_len = payload_len;

        total += enc_len + dec_len;
        if (i == 0) {
            total += (uint8_t)dec[0] + (uint8_t)dec[dec_len - 1];
        }
    }

    printf("%lld\n", (long long)total);

    free(payload);
    free(enc);
    free(dec);
    return 0;
}
