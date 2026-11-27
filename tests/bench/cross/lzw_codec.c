#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum {
    LZW_CLEAR = 256,
    LZW_EOF = 257,
    LZW_MAX_WIDTH = 12,
    LZW_MAX_CODE = 4095,
    LZW_INVALID = 65535
};

typedef struct {
    uint8_t *data;
    size_t len;
    size_t cap;
} ByteBuf;

static void buf_init(ByteBuf *b, size_t init_cap) {
    b->data = (uint8_t *)malloc(init_cap);
    if (!b->data) exit(1);
    b->len = 0;
    b->cap = init_cap;
}

static void buf_push(ByteBuf *b, uint8_t v) {
    if (b->len == b->cap) {
        b->cap *= 2;
        uint8_t *nb = (uint8_t *)realloc(b->data, b->cap);
        if (!nb) exit(1);
        b->data = nb;
    }
    b->data[b->len++] = v;
}

static void emit_lsb(ByteBuf *out, uint32_t code, uint32_t width, uint32_t *bits, uint32_t *nbits) {
    *bits |= code << *nbits;
    *nbits += width;
    while (*nbits >= 8) {
        buf_push(out, (uint8_t)(*bits & 0xFFu));
        *bits >>= 8;
        *nbits -= 8;
    }
}

static uint8_t *lzw_encode(const uint8_t *src, size_t src_len, size_t *out_len) {
    ByteBuf out;
    buf_init(&out, src_len + 64);

    uint32_t width = 9;
    uint32_t hi = LZW_EOF;
    uint32_t overflow = 1u << width;
    uint32_t bits = 0;
    uint32_t nbits = 0;

    uint16_t head[4096];
    uint32_t keys[4096];
    uint16_t vals[4096];
    uint16_t next[4096];
    memset(head, 0, sizeof(head));
    uint16_t entry_count = 0;

    uint32_t saved = LZW_INVALID;
    size_t i = 0;
    if (src_len > 0) {
        emit_lsb(&out, LZW_CLEAR, width, &bits, &nbits);
        saved = src[0];
        i = 1;
    }

    while (i < src_len) {
        uint32_t lit = src[i];
        uint32_t key = (saved << 8) | lit;
        uint32_t h = (key * 31u) & 4095u;
        int found = -1;
        uint16_t cur = head[h];
        while (cur > 0) {
            uint16_t idx = (uint16_t)(cur - 1u);
            if (keys[idx] == key) {
                found = (int)idx;
                break;
            }
            cur = next[idx];
        }
        if (found >= 0) {
            saved = vals[found];
            i++;
            continue;
        }
        emit_lsb(&out, saved, width, &bits, &nbits);
        saved = lit;
        hi++;
        int out_of = 0;
        if (hi == overflow) {
            width++;
            overflow <<= 1;
        }
        if (hi == LZW_MAX_CODE) {
            emit_lsb(&out, LZW_CLEAR, width, &bits, &nbits);
            width = 9;
            hi = LZW_EOF;
            overflow = LZW_CLEAR * 2u;
            memset(head, 0, sizeof(head));
            entry_count = 0;
            out_of = 1;
        }
        if (!out_of) {
            uint16_t idx = entry_count++;
            keys[idx] = key;
            vals[idx] = (uint16_t)hi;
            next[idx] = head[h];
            head[h] = entry_count;
        }
        i++;
    }

    if (saved != LZW_INVALID) {
        emit_lsb(&out, saved, width, &bits, &nbits);
        hi++;
        if (hi == overflow) {
            width++;
            overflow <<= 1;
        }
        if (hi == LZW_MAX_CODE) {
            emit_lsb(&out, LZW_CLEAR, width, &bits, &nbits);
            width = 9;
            hi = LZW_EOF;
            overflow = LZW_CLEAR * 2u;
        }
    } else {
        emit_lsb(&out, LZW_CLEAR, width, &bits, &nbits);
    }

    emit_lsb(&out, LZW_EOF, width, &bits, &nbits);
    if (nbits > 0) {
        buf_push(&out, (uint8_t)(bits & 0xFFu));
    }

    *out_len = out.len;
    return out.data;
}

static uint8_t *lzw_decode(const uint8_t *src, size_t src_len, size_t *out_len) {
    ByteBuf out;
    buf_init(&out, src_len * 4 + 64);

    uint32_t width = 9;
    uint32_t hi = LZW_EOF;
    uint32_t overflow = 1u << width;
    uint32_t last = LZW_INVALID;
    uint32_t bits = 0;
    uint32_t nbits = 0;
    size_t pos = 0;

    uint16_t prefix[4096];
    uint8_t suffix[4096];
    uint8_t stack[4096];
    memset(prefix, 0, sizeof(prefix));
    memset(suffix, 0, sizeof(suffix));

    for (;;) {
        while (nbits < width) {
            if (pos >= src_len) exit(1);
            bits |= ((uint32_t)src[pos++]) << nbits;
            nbits += 8;
        }
        uint32_t code = bits & ((1u << width) - 1u);
        bits >>= width;
        nbits -= width;

        if (code < LZW_CLEAR) {
            buf_push(&out, (uint8_t)code);
            if (last != LZW_INVALID) {
                suffix[hi] = (uint8_t)code;
                prefix[hi] = (uint16_t)last;
            }
        } else {
            if (code == LZW_CLEAR) {
                width = 9;
                hi = LZW_EOF;
                overflow = 1u << width;
                last = LZW_INVALID;
                continue;
            }
            if (code == LZW_EOF) {
                break;
            }
            if (code > hi) exit(1);

            size_t sp = 0;
            uint32_t c = code;
            if (code == hi && last != LZW_INVALID) {
                c = last;
                while (c >= LZW_CLEAR) {
                    c = prefix[c];
                }
                stack[sp++] = (uint8_t)c;
                c = last;
            }
            while (c >= LZW_CLEAR) {
                stack[sp++] = suffix[c];
                c = prefix[c];
            }
            stack[sp++] = (uint8_t)c;

            uint8_t first_byte = stack[sp - 1];
            while (sp > 0) {
                buf_push(&out, stack[--sp]);
            }
            if (last != LZW_INVALID) {
                suffix[hi] = first_byte;
                prefix[hi] = (uint16_t)last;
            }
        }

        last = code;
        hi++;
        if (hi >= overflow) {
            if (width == LZW_MAX_WIDTH) {
                last = LZW_INVALID;
                hi--;
            } else {
                width++;
                overflow <<= 1;
            }
        }
    }

    *out_len = out.len;
    return out.data;
}

int main(void) {
    const char *base = "TOBEORNOTTOBEORTOBEORNOT#";
    size_t base_len = strlen(base);
    size_t payload_len = base_len * 16;
    uint8_t *payload = (uint8_t *)malloc(payload_len);
    if (!payload) return 1;
    for (size_t k = 0; k < 16; k++) {
        memcpy(payload + k * base_len, base, base_len);
    }

    int64_t total = 0;
    for (int i = 0; i < 2500; i++) {
        size_t enc_len = 0;
        uint8_t *enc = lzw_encode(payload, payload_len, &enc_len);
        size_t dec_len = 0;
        uint8_t *dec = lzw_decode(enc, enc_len, &dec_len);
        total += (int64_t)enc_len + (int64_t)dec_len;
        if (i == 0) {
            total += (int64_t)dec[0] + (int64_t)dec[dec_len - 1];
        }
        free(enc);
        free(dec);
    }
    free(payload);
    printf("%lld\n", (long long)total);
    return 0;
}
