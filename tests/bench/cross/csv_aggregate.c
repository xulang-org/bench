#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    const char *prefixes[16] = {
        "tokyo", "oslo", "lima", "cairo", "paris", "rome", "zurich", "seoul",
        "bergen", "kyoto", "milan", "vienna", "prague", "dublin", "lisbon", "athens"
    };

    int64_t st_bytes[1024];
    int64_t st_off[64];
    int64_t st_len[64];
    int64_t st_pos = 0;
    for (int64_t i = 0; i < 64; i++) {
        const char *p = prefixes[i & 15];
        st_off[i] = st_pos;
        for (int64_t ci = 0; p[ci] != '\0'; ci++) {
            st_bytes[st_pos++] = (int64_t)(unsigned char)p[ci];
        }
        st_bytes[st_pos++] = 95;
        st_bytes[st_pos++] = 48 + (i / 10);
        st_bytes[st_pos++] = 48 + (i % 10);
        st_len[i] = st_pos - st_off[i];
    }

    int64_t *buf = (int64_t *)malloc(1600000 * sizeof(int64_t));
    int64_t n = 0;
    int64_t digs[16];
    int64_t rng = 135792468;
    for (int64_t ri = 0; ri < 100000; ri++) {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        int64_t si = (rng >> 10) & 63;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        int64_t temp = (rng % 1999) - 999;
        int64_t off = st_off[si];
        int64_t ln = st_len[si];
        for (int64_t k = 0; k < ln; k++) {
            buf[n++] = st_bytes[off + k];
        }
        buf[n++] = 59;
        int64_t av = temp;
        if (av < 0) {
            buf[n++] = 45;
            av = -av;
        }
        int64_t whole = av / 10;
        if (whole == 0) {
            buf[n++] = 48;
        } else {
            int64_t w = whole;
            int64_t dc = 0;
            while (w > 0) {
                digs[dc++] = 48 + (w % 10);
                w /= 10;
            }
            for (int64_t di = dc - 1; di >= 0; di--) {
                buf[n++] = digs[di];
            }
        }
        buf[n++] = 46;
        buf[n++] = 48 + (av % 10);
        buf[n++] = 10;
    }

    int64_t first_dot = 0;
    while (first_dot < n && buf[first_dot] != 46) {
        first_dot += 1;
    }
    int64_t orig_frac = buf[first_dot + 1] - 48;

    const int64_t CAP = 256;
    const int64_t MASK = 255;
    int64_t k_start[256], k_len[256], st_min[256], st_max[256], st_sum[256], st_cnt[256], occ[256];

    int64_t tot_rows = 0;
    int64_t tot_ck = 0;
    for (int64_t rd = 0; rd < 10; rd++) {
        buf[first_dot + 1] = 48 + ((orig_frac + rd) % 10);
        for (int64_t i = 0; i < CAP; i++) {
            k_start[i] = -1;
        }
        int64_t pos = 0;
        int64_t rows = 0;
        while (pos < n) {
            int64_t s_start = pos;
            int64_t h = 0;
            while (buf[pos] != 59) {
                h = (h * 131 + buf[pos]) & 2147483647;
                pos += 1;
            }
            int64_t s_len = pos - s_start;
            pos += 1;
            int neg = 0;
            if (buf[pos] == 45) {
                neg = 1;
                pos += 1;
            }
            int64_t v = 0;
            while (buf[pos] != 46) {
                v = v * 10 + (buf[pos] - 48);
                pos += 1;
            }
            pos += 1;
            v = v * 10 + (buf[pos] - 48);
            pos += 1;
            if (neg) v = -v;
            if (pos < n && buf[pos] == 10) pos += 1;
            rows += 1;

            int64_t slot = h & MASK;
            while (1) {
                int64_t ks = k_start[slot];
                if (ks == -1) {
                    k_start[slot] = s_start;
                    k_len[slot] = s_len;
                    st_min[slot] = v;
                    st_max[slot] = v;
                    st_sum[slot] = v;
                    st_cnt[slot] = 1;
                    break;
                }
                if (k_len[slot] == s_len) {
                    int eq = 1;
                    for (int64_t ci = 0; ci < s_len; ci++) {
                        if (buf[ks + ci] != buf[s_start + ci]) {
                            eq = 0;
                            break;
                        }
                    }
                    if (eq) {
                        if (v < st_min[slot]) st_min[slot] = v;
                        if (v > st_max[slot]) st_max[slot] = v;
                        st_sum[slot] += v;
                        st_cnt[slot] += 1;
                        break;
                    }
                }
                slot = (slot + 1) & MASK;
            }
        }

        int64_t occ_len = 0;
        for (int64_t i = 0; i < CAP; i++) {
            if (k_start[i] != -1) {
                occ[occ_len++] = i;
            }
        }
        for (int64_t i = 1; i < occ_len; i++) {
            int64_t key_slot = occ[i];
            int64_t j = i - 1;
            while (j >= 0) {
                int64_t a = occ[j];
                int64_t la = k_len[a];
                int64_t lb = k_len[key_slot];
                int64_t ml = la < lb ? la : lb;
                int64_t cmp = 0;
                for (int64_t t = 0; t < ml; t++) {
                    int64_t ba = buf[k_start[a] + t];
                    int64_t bb = buf[k_start[key_slot] + t];
                    if (ba != bb) {
                        cmp = (ba < bb) ? -1 : 1;
                        break;
                    }
                }
                if (cmp == 0) {
                    if (la < lb) cmp = -1;
                    else if (la > lb) cmp = 1;
                }
                if (cmp > 0) {
                    occ[j + 1] = occ[j];
                    j -= 1;
                } else {
                    break;
                }
            }
            occ[j + 1] = key_slot;
        }

        int64_t ck = 0;
        for (int64_t i = 0; i < occ_len; i++) {
            int64_t sl = occ[i];
            int64_t s_mod = st_sum[sl] % 1000000007;
            if (s_mod < 0) s_mod += 1000000007;
            int64_t term = ((i + 1) * 7 + (st_min[sl] + 1000) * 13 + (st_max[sl] + 1000) * 17 + st_cnt[sl] * 19 + s_mod) % 1000000007;
            ck = (ck * 1000003 + term) % 1000000007;
        }
        tot_rows += rows;
        tot_ck = (tot_ck * 31 + ck) % 1000000007;
    }

    free(buf);
    printf("%" PRId64 "\n%" PRId64 "\n", tot_rows, tot_ck);
    return 0;
}
