#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MOD_V 1000000007LL

static int64_t crc32_slice(const int64_t *crc_tbl, const int64_t *buf, int start, int length) {
    const int64_t mask32 = 4294967295LL;
    int64_t c = mask32;
    int end = start + length;
    for (int i = start; i < end; i++) {
        int idx = (int)((c ^ buf[i]) & 255LL);
        c = crc_tbl[idx] ^ (c >> 8);
    }
    return c ^ mask32;
}

static void kv_put(int64_t *kv_key, int64_t *kv_val, int64_t k, int64_t v) {
    const int64_t kv_mask = 8191;
    int slot = (int)(((k * 2654435761LL) >> 16) & kv_mask);
    int first_tomb = -1;
    while (1) {
        int64_t cur = kv_key[slot];
        if (cur == k) {
            kv_val[slot] = v;
            return;
        }
        if (cur == -1) {
            int dst = (first_tomb != -1) ? first_tomb : slot;
            kv_key[dst] = k;
            kv_val[dst] = v;
            return;
        }
        if (cur == -2 && first_tomb == -1) {
            first_tomb = slot;
        }
        slot = (slot + 1) & (int)kv_mask;
    }
}

static void kv_del(int64_t *kv_key, int64_t *kv_val, int64_t k) {
    const int64_t kv_mask = 8191;
    int slot = (int)(((k * 2654435761LL) >> 16) & kv_mask);
    while (1) {
        int64_t cur = kv_key[slot];
        if (cur == -1) {
            return;
        }
        if (cur == k) {
            kv_key[slot] = -2;
            kv_val[slot] = 0;
            return;
        }
        slot = (slot + 1) & (int)kv_mask;
    }
}

static int64_t kv_get(const int64_t *kv_key, const int64_t *kv_val, int64_t k) {
    const int64_t kv_mask = 8191;
    int slot = (int)(((k * 2654435761LL) >> 16) & kv_mask);
    while (1) {
        int64_t cur = kv_key[slot];
        if (cur == -1) {
            return -1;
        }
        if (cur == k) {
            return kv_val[slot];
        }
        slot = (slot + 1) & (int)kv_mask;
    }
}

int main(void) {
    const int64_t poly = 3988292384LL;
    int64_t crc_tbl[256];
    for (int i = 0; i < 256; i++) {
        int64_t c = i;
        for (int b = 0; b < 8; b++) {
            if ((c & 1LL) != 0) {
                c = poly ^ (c >> 1);
            } else {
                c = c >> 1;
            }
        }
        crc_tbl[i] = c;
    }

    const int kv_cap = 8192;
    int64_t *kv_key = (int64_t *)malloc((size_t)kv_cap * sizeof(int64_t));
    int64_t *kv_val = (int64_t *)calloc((size_t)kv_cap, sizeof(int64_t));
    for (int i = 0; i < kv_cap; i++) {
        kv_key[i] = -1;
    }

    int64_t *buf = (int64_t *)malloc(180000U * sizeof(int64_t));
    int64_t rng = 999888777LL;
    int64_t lsn = 1;
    int64_t replayed = 0;
    int64_t ck = 0;

    for (int seg = 0; seg < 40; seg++) {
        int blen = 0;
        for (int rec = 0; rec < 3000; rec++) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t op = ((rng % 6LL) == 0) ? 2 : 1;
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t key = rng % 4096LL;
            int64_t vlen = 0;
            if (op == 1) {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                vlen = 8LL + (rng % 32LL);
            }
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t seed = (rng >> 4) & 255LL;

            int rec_start = blen;
            buf[blen] = 87;
            buf[blen + 1] = 76;
            buf[blen + 2] = op;
            buf[blen + 3] = (lsn ^ key) & 255LL;
            buf[blen + 4] = lsn & 255LL;
            buf[blen + 5] = (lsn >> 8) & 255LL;
            buf[blen + 6] = (lsn >> 16) & 255LL;
            buf[blen + 7] = (lsn >> 24) & 255LL;
            buf[blen + 8] = key & 255LL;
            buf[blen + 9] = (key >> 8) & 255LL;
            buf[blen + 10] = (key >> 16) & 255LL;
            buf[blen + 11] = (key >> 24) & 255LL;
            buf[blen + 12] = vlen & 255LL;
            buf[blen + 13] = (vlen >> 8) & 255LL;
            blen += 14;
            int vl = (int)vlen;
            for (int j = 0; j < vl; j++) {
                buf[blen++] = (seed + (int64_t)j * 13LL + lsn) & 255LL;
            }
            int64_t crc = crc32_slice(crc_tbl, buf, rec_start, 14 + vl);
            buf[blen] = crc & 255LL;
            buf[blen + 1] = (crc >> 8) & 255LL;
            buf[blen + 2] = (crc >> 16) & 255LL;
            buf[blen + 3] = (crc >> 24) & 255LL;
            blen += 4;
            lsn++;
        }

        if ((seg % 4) == 3) {
            blen -= 7;
        } else if ((seg % 5) == 4) {
            buf[blen - 2] ^= 1LL;
        }

        int pos = 0;
        int64_t seg_rep = 0;
        int64_t early = 0;
        while (pos < blen) {
            if (pos + 18 > blen) {
                early = 1;
                break;
            }
            if (buf[pos] != 87 || buf[pos + 1] != 76) {
                early = 1;
                break;
            }
            int64_t op = buf[pos + 2];
            if (op != 1 && op != 2) {
                early = 1;
                break;
            }
            int vlen = (int)(buf[pos + 12] | (buf[pos + 13] << 8));
            if (pos + 18 + vlen > blen) {
                early = 1;
                break;
            }
            int64_t stored = buf[pos + 14 + vlen] | (buf[pos + 15 + vlen] << 8) | (buf[pos + 16 + vlen] << 16) | (buf[pos + 17 + vlen] << 24);
            int64_t calc = crc32_slice(crc_tbl, buf, pos, 14 + vlen);
            if (calc != stored) {
                early = 1;
                break;
            }
            int64_t key = buf[pos + 8] | (buf[pos + 9] << 8) | (buf[pos + 10] << 16) | (buf[pos + 11] << 24);
            if (op == 1) {
                int64_t vh = 0;
                for (int j = 0; j < vlen; j++) {
                    vh = (vh * 131LL + buf[pos + 14 + j]) % MOD_V;
                }
                kv_put(kv_key, kv_val, key, vh);
            } else {
                kv_del(kv_key, kv_val, key);
            }
            seg_rep++;
            pos += 18 + vlen;
        }
        replayed += seg_rep;
        ck = (ck * 37LL + (int64_t)seg * 1009LL + seg_rep * 17LL + early) % MOD_V;
    }

    for (int64_t k = 0; k < 4096; k++) {
        int64_t v = kv_get(kv_key, kv_val, k);
        if (v >= 0) {
            ck = (ck * 31LL + k * 97LL + v) % MOD_V;
        }
    }

    printf("%" PRId64 "\n%" PRId64 "\n", replayed, ck);
    free(kv_key);
    free(kv_val);
    free(buf);
    return 0;
}
