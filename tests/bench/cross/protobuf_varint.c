#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MOD_V 1000000007LL

typedef struct {
    int64_t *data;
    int len;
    int cap;
} Vec64;

static void vec_init(Vec64 *v, int cap) {
    v->data = (int64_t *)malloc((size_t)cap * sizeof(int64_t));
    v->len = 0;
    v->cap = cap;
}

static void vec_push(Vec64 *v, int64_t x) {
    if (v->len == v->cap) {
        v->cap *= 2;
        v->data = (int64_t *)realloc(v->data, (size_t)v->cap * sizeof(int64_t));
    }
    v->data[v->len++] = x;
}

static void put_uvarint(Vec64 *buf, int64_t val) {
    uint64_t v = (uint64_t)val;
    while (v >= 128ULL) {
        vec_push(buf, (int64_t)((v & 127ULL) | 128ULL));
        v >>= 7;
    }
    vec_push(buf, (int64_t)(v & 127ULL));
}

static int64_t zigzag_enc(int64_t v) {
    if (v >= 0) return (int64_t)((uint64_t)v << 1);
    return (int64_t)(((uint64_t)(-v) << 1) - 1ULL);
}

static int64_t zigzag_dec(int64_t u) {
    uint64_t uu = (uint64_t)u;
    if ((uu & 1ULL) == 0ULL) return (int64_t)(uu >> 1);
    return -(int64_t)((uu >> 1) + 1ULL);
}

static void push_str_bytes(Vec64 *buf, const char *s) {
    while (*s) {
        vec_push(buf, (int64_t)(unsigned char)(*s));
        s++;
    }
}

int main(void) {
    const char *symbols[8] = {"BTC-USD", "ETH-EUR", "SOL-JPY", "XU-USD", "NVDA", "AAPL", "GOOG", "MSFT"};
    const char *tags[8] = {"fast", "batch", "edge", "core", "prod", "canary", "blue", "green"};

    Vec64 buf, meta, packed, msg;
    vec_init(&buf, 32768);
    vec_init(&meta, 64);
    vec_init(&packed, 32);
    vec_init(&msg, 128);
    int64_t qs[8];

    int64_t rng = 314159265;
    int64_t total_wire = 0, ck = 0;
    for (int64_t batch = 0; batch < 400; batch++) {
        buf.len = 0;
        for (int64_t i = 0; i < 500; i++) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t order_id = (batch * 500 + i + 1) * 131 + (rng & 1023);
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t price_delta = (rng % 200001) - 100000;
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            const char *sym = symbols[rng & 7];
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int qcnt = (int)(4 + (rng & 3));
            for (int qi = 0; qi < qcnt; qi++) {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                qs[qi] = 1 + (rng % 5000);
            }
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t reg_id = 1 + (rng & 31);
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t lat_us = (rng % 10001) - 5000;
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            const char *tag = tags[rng & 7];

            int sym_len = 0;
            while (sym[sym_len]) sym_len++;
            int tag_len = 0;
            while (tag[tag_len]) tag_len++;

            meta.len = 0;
            put_uvarint(&meta, (1 << 3) | 0);
            put_uvarint(&meta, reg_id);
            put_uvarint(&meta, (2 << 3) | 0);
            put_uvarint(&meta, zigzag_enc(lat_us));
            put_uvarint(&meta, (3 << 3) | 2);
            put_uvarint(&meta, tag_len);
            push_str_bytes(&meta, tag);

            packed.len = 0;
            for (int qi = 0; qi < qcnt; qi++) put_uvarint(&packed, qs[qi]);

            msg.len = 0;
            put_uvarint(&msg, (1 << 3) | 0);
            put_uvarint(&msg, order_id);
            put_uvarint(&msg, (2 << 3) | 0);
            put_uvarint(&msg, zigzag_enc(price_delta));
            put_uvarint(&msg, (3 << 3) | 2);
            put_uvarint(&msg, sym_len);
            push_str_bytes(&msg, sym);
            put_uvarint(&msg, (4 << 3) | 2);
            put_uvarint(&msg, packed.len);
            for (int k = 0; k < packed.len; k++) vec_push(&msg, packed.data[k]);
            put_uvarint(&msg, (5 << 3) | 2);
            put_uvarint(&msg, meta.len);
            for (int k = 0; k < meta.len; k++) vec_push(&msg, meta.data[k]);

            put_uvarint(&buf, msg.len);
            for (int k = 0; k < msg.len; k++) vec_push(&buf, msg.data[k]);
        }

        total_wire += buf.len;
        const int64_t *bd = buf.data;
        int pos = 0, blen = buf.len;
        while (pos < blen) {
            int64_t mlen = 0;
            int sh = 0;
            for (;;) {
                int64_t b = bd[pos++];
                mlen |= (b & 127) << sh;
                if ((b & 128) == 0) break;
                sh += 7;
            }
            int end = pos + (int)mlen;
            int64_t oid = 0, pdelta = 0, sym_sum = 0, q_sum = 0, reg = 0, lat = 0, tlen = 0;
            while (pos < end) {
                int64_t tag_w = 0;
                sh = 0;
                for (;;) {
                    int64_t b = bd[pos++];
                    tag_w |= (b & 127) << sh;
                    if ((b & 128) == 0) break;
                    sh += 7;
                }
                int64_t fnum = tag_w >> 3;
                int64_t wtype = tag_w & 7;
                if (wtype == 0) {
                    int64_t val = 0;
                    sh = 0;
                    for (;;) {
                        int64_t b = bd[pos++];
                        val |= (b & 127) << sh;
                        if ((b & 128) == 0) break;
                        sh += 7;
                    }
                    if (fnum == 1) oid = val;
                    else if (fnum == 2) pdelta = zigzag_dec(val);
                } else if (wtype == 2) {
                    int64_t ln = 0;
                    sh = 0;
                    for (;;) {
                        int64_t b = bd[pos++];
                        ln |= (b & 127) << sh;
                        if ((b & 128) == 0) break;
                        sh += 7;
                    }
                    int sub_end = pos + (int)ln;
                    if (fnum == 3) {
                        while (pos < sub_end) sym_sum += bd[pos++];
                    } else if (fnum == 4) {
                        while (pos < sub_end) {
                            int64_t qv = 0;
                            sh = 0;
                            for (;;) {
                                int64_t b = bd[pos++];
                                qv |= (b & 127) << sh;
                                if ((b & 128) == 0) break;
                                sh += 7;
                            }
                            q_sum += qv;
                        }
                    } else if (fnum == 5) {
                        while (pos < sub_end) {
                            int64_t mtag = 0;
                            sh = 0;
                            for (;;) {
                                int64_t b = bd[pos++];
                                mtag |= (b & 127) << sh;
                                if ((b & 128) == 0) break;
                                sh += 7;
                            }
                            int64_t mf = mtag >> 3;
                            int64_t mw = mtag & 7;
                            if (mw == 0) {
                                int64_t mv = 0;
                                sh = 0;
                                for (;;) {
                                    int64_t b = bd[pos++];
                                    mv |= (b & 127) << sh;
                                    if ((b & 128) == 0) break;
                                    sh += 7;
                                }
                                if (mf == 1) reg = mv;
                                else if (mf == 2) lat = zigzag_dec(mv);
                            } else if (mw == 2) {
                                int64_t sln = 0;
                                sh = 0;
                                for (;;) {
                                    int64_t b = bd[pos++];
                                    sln |= (b & 127) << sh;
                                    if ((b & 128) == 0) break;
                                    sh += 7;
                                }
                                if (mf == 3) tlen = sln;
                                pos += (int)sln;
                            }
                        }
                    } else {
                        pos = sub_end;
                    }
                }
            }
            int64_t row = (oid + pdelta + sym_sum + q_sum + reg * 13 + lat + tlen * 7) % MOD_V;
            if (row < 0) row += MOD_V;
            ck = (ck * 31 + row) % MOD_V;
        }
    }
    free(buf.data);
    free(meta.data);
    free(packed.data);
    free(msg.data);
    printf("%" PRId64 "\n%" PRId64 "\n", total_wire, ck);
    return 0;
}
