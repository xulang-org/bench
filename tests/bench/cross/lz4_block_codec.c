#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MOD_V 1000000007LL

static int lz4_compress(const int64_t *blocks, int src_off, int n, int *ht, int64_t *comp) {
    for (int i = 0; i < 4096; i++) {
        ht[i] = -1;
    }
    int op = 0;
    int ip = 0;
    int anchor = 0;
    int limit = n - 12;
    int mflimit = n - 5;
    while (ip < limit) {
        int p = src_off + ip;
        int64_t seq = blocks[p] | (blocks[p + 1] << 8) | (blocks[p + 2] << 16) | (blocks[p + 3] << 24);
        int h = (int)(((seq * 73244475LL) >> 18) & 4095LL);
        int ref = ht[h];
        ht[h] = ip;
        if (ref >= 0 && (ip - ref) <= 65535) {
            int rp = src_off + ref;
            if (blocks[rp] == blocks[p] && blocks[rp + 1] == blocks[p + 1] &&
                blocks[rp + 2] == blocks[p + 2] && blocks[rp + 3] == blocks[p + 3]) {
                int mlen = 4;
                while (ip + mlen < mflimit && blocks[rp + mlen] == blocks[p + mlen]) {
                    mlen++;
                }
                int lit_len = ip - anchor;
                int m_extra = mlen - 4;
                int tok_lit = (lit_len >= 15) ? 15 : lit_len;
                int tok_m = (m_extra >= 15) ? 15 : m_extra;
                comp[op++] = (tok_lit << 4) | tok_m;
                if (lit_len >= 15) {
                    int rem = lit_len - 15;
                    while (rem >= 255) {
                        comp[op++] = 255;
                        rem -= 255;
                    }
                    comp[op++] = rem;
                }
                for (int j = 0; j < lit_len; j++) {
                    comp[op++] = blocks[src_off + anchor + j];
                }
                int off = ip - ref;
                comp[op++] = off & 255;
                comp[op++] = (off >> 8) & 255;
                if (m_extra >= 15) {
                    int rem = m_extra - 15;
                    while (rem >= 255) {
                        comp[op++] = 255;
                        rem -= 255;
                    }
                    comp[op++] = rem;
                }
                ip += mlen;
                anchor = ip;
                continue;
            }
        }
        ip++;
    }
    int lit_len = n - anchor;
    int tok_lit = (lit_len >= 15) ? 15 : lit_len;
    comp[op++] = tok_lit << 4;
    if (lit_len >= 15) {
        int rem = lit_len - 15;
        while (rem >= 255) {
            comp[op++] = 255;
            rem -= 255;
        }
        comp[op++] = rem;
    }
    for (int j = 0; j < lit_len; j++) {
        comp[op++] = blocks[src_off + anchor + j];
    }
    return op;
}

static void lz4_decompress(const int64_t *comp, int clen, int64_t *decomp) {
    int ip = 0;
    int op = 0;
    while (ip < clen) {
        int tok = (int)comp[ip++];
        int lit_len = tok >> 4;
        if (lit_len == 15) {
            while (1) {
                int b = (int)comp[ip++];
                lit_len += b;
                if (b != 255) {
                    break;
                }
            }
        }
        for (int j = 0; j < lit_len; j++) {
            decomp[op++] = comp[ip++];
        }
        if (ip >= clen) {
            break;
        }
        int off = (int)(comp[ip] | (comp[ip + 1] << 8));
        ip += 2;
        int mlen = (tok & 15) + 4;
        if ((tok & 15) == 15) {
            while (1) {
                int b = (int)comp[ip++];
                mlen += b;
                if (b != 255) {
                    break;
                }
            }
        }
        int mp = op - off;
        for (int j = 0; j < mlen; j++) {
            decomp[op++] = decomp[mp + j];
        }
    }
}

int main(void) {
    const int blk_len = 32768;
    int64_t rng = 135724680LL;
    static const char *phrases[6] = {
        "{\"level\":\"INFO\",\"service\":\"storage-node\",\"msg\":\"compaction_ok\",\"ms\":",
        "{\"level\":\"WARN\",\"service\":\"rpc-gateway\",\"msg\":\"retry_backoff\",\"ms\":",
        "SELECT region, category, SUM(amount) FROM orders WHERE status = 1; ",
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
        "GET /api/v1/users/profile HTTP/1.1\r\nHost: api.xulang.org\r\n\r\n",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    };

    int64_t *blocks = (int64_t *)malloc((size_t)(24 * blk_len) * sizeof(int64_t));
    int64_t *src = (int64_t *)malloc((size_t)(blk_len + 256) * sizeof(int64_t));

    for (int bi = 0; bi < 24; bi++) {
        int slen = 0;
        while (slen < blk_len) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int k = (int)(rng % 10LL);
            if (k < 6) {
                const char *ps = phrases[k];
                int plen = (int)strlen(ps);
                for (int i = 0; i < plen; i++) {
                    src[slen++] = (int64_t)(unsigned char)ps[i];
                }
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int64_t v = rng % 1000LL;
                src[slen++] = 48 + (v / 100LL);
                src[slen++] = 48 + ((v / 10LL) % 10LL);
                src[slen++] = 48 + (v % 10LL);
                src[slen++] = 10;
            } else if (k < 8) {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int64_t ch = 65LL + (rng % 26LL);
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int rl = (int)(12LL + (rng % 48LL));
                for (int j = 0; j < rl; j++) {
                    src[slen++] = ch;
                }
            } else {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int rl = (int)(8LL + (rng % 24LL));
                for (int j = 0; j < rl; j++) {
                    rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                    src[slen++] = 32LL + (rng % 95LL);
                }
            }
        }
        memcpy(blocks + bi * blk_len, src, (size_t)blk_len * sizeof(int64_t));
    }
    free(src);

    int ht[4096];
    int64_t *comp = (int64_t *)malloc((size_t)(blk_len + 4096) * sizeof(int64_t));
    int64_t *decomp = (int64_t *)malloc((size_t)blk_len * sizeof(int64_t));

    int64_t total_comp = 0;
    int64_t ck = 0;
    for (int rnd = 0; rnd < 4; rnd++) {
        for (int bi = 0; bi < 24; bi++) {
            int clen = lz4_compress(blocks, bi * blk_len, blk_len, ht, comp);
            lz4_decompress(comp, clen, decomp);
            int64_t h = clen;
            for (int i = 0; i < blk_len; i++) {
                h = (h * 131LL + decomp[i]) % MOD_V;
            }
            total_comp += clen;
            ck = (ck * 31LL + h) % MOD_V;
        }
    }

    printf("%" PRId64 "\n%" PRId64 "\n", total_comp, ck);
    free(blocks);
    free(comp);
    free(decomp);
    return 0;
}
