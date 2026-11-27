#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static inline int64_t lcg(int64_t seed) {
    return (seed * 1103515245 + 12345) & 2147483647;
}

int main(void) {
    const int n = 200000;
    const int q = 200000;
    int64_t *st = (int64_t *)malloc((size_t)n * sizeof(int64_t));
    int64_t *en = (int64_t *)malloc((size_t)n * sizeof(int64_t));
    int64_t *max_en = (int64_t *)calloc((size_t)n, sizeof(int64_t));
    int64_t *qst = (int64_t *)malloc((size_t)q * sizeof(int64_t));
    int64_t *qen = (int64_t *)malloc((size_t)q * sizeof(int64_t));
    if (!st || !en || !max_en || !qst || !qen) return 1;

    int64_t seed = 123456789;
    int64_t cur_st = 0;
    for (int i = 0; i < n; i++) {
        seed = lcg(seed);
        cur_st += seed % 100;
        seed = lcg(seed);
        int64_t ln = 1 + (seed % 5000);
        st[i] = cur_st;
        en[i] = cur_st + ln;
    }
    int64_t max_coord = cur_st + 1;

    for (int i = 0; i < q; i++) {
        seed = lcg(seed);
        int64_t qs = seed % max_coord;
        seed = lcg(seed);
        int64_t ln = 1 + (seed % 5000);
        qst[i] = qs;
        qen[i] = qs + ln;
    }

    for (int i = 0; i < n; i += 2) {
        max_en[i] = en[i];
    }
    int k = 1;
    while ((1 << k) <= n) {
        int x = 1 << (k - 1);
        int i0 = (x << 1) - 1;
        int step = x << 2;
        for (int i = i0; i < n; i += step) {
            int64_t el = max_en[i - x];
            int64_t er;
            if (i + x < n) {
                er = max_en[i + x];
            } else {
                er = en[i];
                int lim = i + (x << 1);
                if (lim > n) lim = n;
                for (int j = i + 1; j < lim; j++) {
                    if (en[j] > er) er = en[j];
                }
            }
            int64_t e = en[i];
            if (el > e) e = el;
            if (er > e) e = er;
            max_en[i] = e;
        }
        k++;
    }
    int max_k = k - 1;

    int sk[64], sx[64], sw[64];
    int64_t hits = 0;
    int64_t cov_sum = 0;
    int root_x = (1 << max_k) - 1;

    for (int qi = 0; qi < q; qi++) {
        int64_t qs = qst[qi];
        int64_t qe = qen[qi];
        sk[0] = max_k;
        sx[0] = root_x;
        sw[0] = 0;
        int sp = 1;
        while (sp > 0) {
            sp--;
            int kk = sk[sp];
            int x = sx[sp];
            int w = sw[sp];
            if (kk <= 3) {
                int i0 = (x >> kk) << kk;
                int i1 = i0 + (1 << (kk + 1)) - 1;
                if (i1 >= n) i1 = n;
                for (int ii = i0; ii < i1 && st[ii] < qe; ii++) {
                    if (qs < en[ii]) {
                        hits++;
                        int64_t os = qs > st[ii] ? qs : st[ii];
                        int64_t oe = qe < en[ii] ? qe : en[ii];
                        cov_sum += oe - os;
                    }
                }
            } else if (w == 0) {
                int y = x - (1 << (kk - 1));
                sk[sp] = kk;
                sx[sp] = x;
                sw[sp] = 1;
                sp++;
                if (y >= n || max_en[y] > qs) {
                    sk[sp] = kk - 1;
                    sx[sp] = y;
                    sw[sp] = 0;
                    sp++;
                }
            } else if (x < n && st[x] < qe) {
                if (qs < en[x]) {
                    hits++;
                    int64_t os = qs > st[x] ? qs : st[x];
                    int64_t oe = qe < en[x] ? qe : en[x];
                    cov_sum += oe - os;
                }
                sk[sp] = kk - 1;
                sx[sp] = x + (1 << (kk - 1));
                sw[sp] = 0;
                sp++;
            }
        }
    }

    printf("%lld\n%lld\n", (long long)hits, (long long)cov_sum);
    free(st);
    free(en);
    free(max_en);
    free(qst);
    free(qen);
    return 0;
}
