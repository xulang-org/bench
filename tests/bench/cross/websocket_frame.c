#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MOD_V 1000000007LL

int main(void) {
    int64_t s_fin[80], s_op[80], s_m0[80], s_m1[80], s_m2[80], s_m3[80], s_len[80], s_seed[80];
    int64_t rng = 987654321;
    for (int i = 0; i < 80; i++) {
        int tier = i % 4;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int64_t ln;
        if (tier == 0) ln = 13 + (rng % 90);
        else if (tier == 1) ln = 126 + (rng % 300);
        else if (tier == 2) ln = 500 + (rng % 1500);
        else ln = 2000 + (rng % 2048);
        int64_t fin = (i % 5) != 0 ? 1 : 0;
        int64_t op = (i & 1) == 0 ? 2 : 1;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        s_m0[i] = (rng >> 8) & 255;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        s_m1[i] = (rng >> 8) & 255;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        s_m2[i] = (rng >> 8) & 255;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        s_m3[i] = (rng >> 8) & 255;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        s_seed[i] = (rng >> 4) & 255;
        s_fin[i] = fin;
        s_op[i] = op;
        s_len[i] = ln;
    }

    int wire_cap = 262144;
    int64_t *wire = (int64_t *)malloc((size_t)wire_cap * sizeof(int64_t));
    int64_t total_bytes = 0, ck = 0;

    for (int64_t rnd = 0; rnd < 180; rnd++) {
        int wlen = 0;
        for (int idx = 0; idx < 80; idx++) {
            int64_t fin = s_fin[idx], op = s_op[idx], ln = s_len[idx], seed = s_seed[idx];
            int64_t m0 = (s_m0[idx] + rnd) & 255;
            int64_t m1 = (s_m1[idx] + idx) & 255;
            int64_t m2 = s_m2[idx], m3 = s_m3[idx];
            if (wlen + (int)ln + 16 > wire_cap) {
                wire_cap *= 2;
                wire = (int64_t *)realloc(wire, (size_t)wire_cap * sizeof(int64_t));
            }
            wire[wlen++] = ((fin & 1) << 7) | (op & 15);
            if (ln <= 125) {
                wire[wlen++] = 128 | ln;
            } else {
                wire[wlen++] = 128 | 126;
                wire[wlen++] = (ln >> 8) & 255;
                wire[wlen++] = ln & 255;
            }
            wire[wlen++] = m0;
            wire[wlen++] = m1;
            wire[wlen++] = m2;
            wire[wlen++] = m3;
            for (int64_t j = 0; j < ln; j++) {
                int64_t pb = (seed + j * 17 + rnd * 3) & 255;
                int64_t mk = m0;
                int64_t rem = j & 3;
                if (rem == 1) mk = m1;
                else if (rem == 2) mk = m2;
                else if (rem == 3) mk = m3;
                wire[wlen++] = pb ^ mk;
            }
        }

        int pos = 0;
        while (pos < wlen) {
            int64_t b0 = wire[pos];
            int64_t b1 = wire[pos + 1];
            pos += 2;
            int64_t fin = (b0 >> 7) & 1;
            int64_t op = b0 & 15;
            int64_t masked = (b1 >> 7) & 1;
            int64_t plen = b1 & 127;
            if (plen == 126) {
                plen = (wire[pos] << 8) | wire[pos + 1];
                pos += 2;
            }
            int64_t m0 = 0, m1 = 0, m2 = 0, m3 = 0;
            if (masked) {
                m0 = wire[pos]; m1 = wire[pos + 1]; m2 = wire[pos + 2]; m3 = wire[pos + 3];
                pos += 4;
            }
            int64_t fh = (fin * 17 + op) % MOD_V;
            for (int j = 0; j < (int)plen; j++) {
                int64_t mk = m0;
                int rem = j & 3;
                if (rem == 1) mk = m1;
                else if (rem == 2) mk = m2;
                else if (rem == 3) mk = m3;
                int64_t ch = wire[pos + j] ^ mk;
                fh = (fh * 131 + ch) % MOD_V;
            }
            pos += (int)plen;
            total_bytes += plen;
            ck = (ck * 31 + fh) % MOD_V;
        }
    }
    free(wire);
    printf("%" PRId64 "\n%" PRId64 "\n", total_bytes, ck);
    return 0;
}
