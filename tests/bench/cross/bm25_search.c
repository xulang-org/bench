#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MOD_V 1000000007LL

static int64_t ilog2_x1000(int64_t x, const int64_t *lut) {
    int64_t b = 0;
    int64_t t = x;
    while (t >= 2) {
        t >>= 1;
        b++;
    }
    int64_t frac = ((x - (1LL << b)) << 4) >> b;
    return b * 1000LL + lut[frac];
}

int main(void) {
    const int n_docs = 6000;
    const int vocab = 2048;
    int64_t rng = 777654321LL;
    static const int64_t lut[16] = {0, 87, 170, 248, 322, 392, 459, 524, 585, 644, 700, 755, 807, 858, 907, 954};

    int64_t *doc_len = (int64_t *)calloc((size_t)n_docs, sizeof(int64_t));
    int64_t *scores = (int64_t *)calloc((size_t)n_docs, sizeof(int64_t));
    int64_t *stamp = (int64_t *)calloc((size_t)n_docs, sizeof(int64_t));
    int *touched = (int *)malloc((size_t)n_docs * sizeof(int));

    int64_t *df = (int64_t *)calloc((size_t)vocab, sizeof(int64_t));
    int *post_off = (int *)calloc((size_t)(vocab + 1), sizeof(int));
    int *cur = (int *)malloc((size_t)vocab * sizeof(int));
    int64_t *idf = (int64_t *)calloc((size_t)vocab, sizeof(int64_t));

    int raw_cap = n_docs * 56;
    int *raw_d = (int *)malloc((size_t)raw_cap * sizeof(int));
    int *raw_t = (int *)malloc((size_t)raw_cap * sizeof(int));
    int64_t *raw_f = (int64_t *)malloc((size_t)raw_cap * sizeof(int64_t));
    int raw_len = 0;
    int tmp[64];

    int64_t total_len = 0;
    for (int d = 0; d < n_docs; d++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int dl = (int)(24 + (rng % 32));
        doc_len[d] = dl;
        total_len += dl;
        for (int j = 0; j < dl; j++) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int term = 0;
            if ((rng % 3) == 0) {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                term = (int)(rng % 64);
            } else {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                term = 64 + (int)(rng % (vocab - 64));
            }
            tmp[j] = term;
        }
        for (int j = 1; j < dl; j++) {
            int key = tmp[j];
            int p = j - 1;
            while (p >= 0 && tmp[p] > key) {
                tmp[p + 1] = tmp[p];
                p--;
            }
            tmp[p + 1] = key;
        }
        int j = 0;
        while (j < dl) {
            int term = tmp[j];
            int cnt = 1;
            while (j + cnt < dl && tmp[j + cnt] == term) {
                cnt++;
            }
            df[term]++;
            raw_d[raw_len] = d;
            raw_t[raw_len] = term;
            raw_f[raw_len] = cnt;
            raw_len++;
            j += cnt;
        }
    }

    for (int t = 0; t < vocab; t++) {
        post_off[t + 1] = post_off[t] + (int)df[t];
        cur[t] = post_off[t];
    }
    int total_p = post_off[vocab];
    int *post_doc = (int *)malloc((size_t)total_p * sizeof(int));
    int64_t *post_tf = (int64_t *)malloc((size_t)total_p * sizeof(int64_t));
    for (int i = 0; i < raw_len; i++) {
        int term = raw_t[i];
        int idx = cur[term];
        post_doc[idx] = raw_d[i];
        post_tf[idx] = raw_f[i];
        cur[term] = idx + 1;
    }

    for (int t = 0; t < vocab; t++) {
        if (df[t] > 0) {
            int64_t ratio_x1024 = (((int64_t)n_docs - df[t]) * 2LL + 1LL) * 1024LL / (df[t] * 2LL + 1LL) + 1024LL;
            idf[t] = ilog2_x1000(ratio_x1024, lut) - 10000LL;
        }
    }

    int64_t avgdl_x100 = (total_len * 100LL) / (int64_t)n_docs;
    int64_t *dl_norm = (int64_t *)malloc((size_t)n_docs * sizeof(int64_t));
    for (int d = 0; d < n_docs; d++) {
        dl_norm[d] = 250LL + (750LL * doc_len[d] * 100LL) / avgdl_x100;
    }

    int qterms[5];
    int top_d[10];
    int64_t top_s[10];
    int64_t total_hits = 0;
    int64_t ck = 0;

    for (int64_t q = 1; q <= 2000; q++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int qn = 3 + (int)(rng % 3);
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        qterms[0] = (int)(rng % 64);
        for (int j = 1; j < qn; j++) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            qterms[j] = 64 + (int)(rng % (vocab - 64));
        }
        int t_cnt = 0;
        for (int j = 0; j < qn; j++) {
            int term = qterms[j];
            int64_t it = idf[term];
            if (it > 0) {
                int pend = post_off[term + 1];
                for (int p = post_off[term]; p < pend; p++) {
                    int doc_i = post_doc[p];
                    int64_t tf = post_tf[p];
                    int64_t sc = (it * tf * 2200LL) / (tf * 1000LL + (12LL * dl_norm[doc_i]) / 10LL);
                    if (stamp[doc_i] != q) {
                        stamp[doc_i] = q;
                        scores[doc_i] = sc;
                        touched[t_cnt++] = doc_i;
                    } else {
                        scores[doc_i] += sc;
                    }
                }
            }
        }
        int k_found = 0;
        for (int i = 0; i < t_cnt; i++) {
            int doc_i = touched[i];
            int64_t s = scores[doc_i];
            if (k_found < 10 || s > top_s[9] || (s == top_s[9] && doc_i < top_d[9])) {
                int pos = 9;
                if (k_found < 10) {
                    pos = k_found++;
                }
                while (pos > 0 && (s > top_s[pos - 1] || (s == top_s[pos - 1] && doc_i < top_d[pos - 1]))) {
                    top_s[pos] = top_s[pos - 1];
                    top_d[pos] = top_d[pos - 1];
                    pos--;
                }
                top_s[pos] = s;
                top_d[pos] = doc_i;
            }
        }
        total_hits += k_found;
        for (int r = 0; r < k_found; r++) {
            ck = (ck * 31LL + (int64_t)top_d[r] * 10007LL + top_s[r]) % MOD_V;
        }
    }

    printf("%" PRId64 "\n%" PRId64 "\n", total_hits, ck);
    free(doc_len);
    free(scores);
    free(stamp);
    free(touched);
    free(df);
    free(post_off);
    free(cur);
    free(idf);
    free(raw_d);
    free(raw_t);
    free(raw_f);
    free(post_doc);
    free(post_tf);
    free(dl_norm);
    return 0;
}
