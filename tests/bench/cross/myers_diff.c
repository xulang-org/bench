#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MOD_V 1000000007LL

int main(void) {
    const int max_d = 120;
    const int stride = 241;
    const int off = 120;

    int *v = (int *)calloc((size_t)stride, sizeof(int));
    int *trace = (int *)calloc((size_t)((max_d + 1) * stride), sizeof(int));
    int64_t a[200];
    int64_t b[300];
    int64_t op_type[600];
    int64_t op_val[600];

    int64_t rng = 20260501LL;
    int64_t total_edits = 0;
    int64_t ck = 0;

    for (int pair = 0; pair < 1200; pair++) {
        int n = 200;
        for (int i = 0; i < n; i++) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t val = rng & 63LL;
            a[i] = val;
            b[i] = val;
        }
        int m = n;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int nmut = (int)(18LL + (rng % 11LL));
        for (int mi = 0; mi < nmut; mi++) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t kind = rng % 3LL;
            if (kind == 0 && m > 120) {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int pos = (int)(rng % (int64_t)m);
                for (int p = pos; p + 1 < m; p++) {
                    b[p] = b[p + 1];
                }
                m--;
            } else if (kind == 1 && m < 260) {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int pos = (int)(rng % (int64_t)(m + 1));
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int64_t nv = rng & 63LL;
                for (int p = m; p > pos; p--) {
                    b[p] = b[p - 1];
                }
                b[pos] = nv;
                m++;
            } else {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int pos = (int)(rng % (int64_t)m);
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                b[pos] = rng & 63LL;
            }
        }

        v[off + 1] = 0;
        int found_d = -1;
        for (int d = 0; d <= max_d; d++) {
            int tbase = d * stride;
            for (int k = -d; k <= d; k += 2) {
                int x;
                if (k == -d || (k != d && v[off + k - 1] < v[off + k + 1])) {
                    x = v[off + k + 1];
                } else {
                    x = v[off + k - 1] + 1;
                }
                int y = x - k;
                while (x < n && y < m && a[x] == b[y]) {
                    x++;
                    y++;
                }
                v[off + k] = x;
                trace[tbase + off + k] = x;
                if (x >= n && y >= m) {
                    found_d = d;
                    break;
                }
            }
            if (found_d >= 0) {
                break;
            }
        }

        int x = n;
        int y = m;
        int oc = 0;
        for (int bd = found_d; bd > 0; bd--) {
            int pbase = (bd - 1) * stride;
            int k = x - y;
            int prev_k;
            if (k == -bd || (k != bd && trace[pbase + off + k - 1] < trace[pbase + off + k + 1])) {
                prev_k = k + 1;
            } else {
                prev_k = k - 1;
            }
            int prev_x = trace[pbase + off + prev_k];
            int prev_y = prev_x - prev_k;
            while (x > prev_x && y > prev_y) {
                op_type[oc] = 0;
                op_val[oc] = a[x - 1];
                oc++;
                x--;
                y--;
            }
            if (x == prev_x) {
                op_type[oc] = 1;
                op_val[oc] = b[y - 1];
                oc++;
                y--;
            } else {
                op_type[oc] = 2;
                op_val[oc] = a[x - 1];
                oc++;
                x--;
            }
        }
        while (x > 0 && y > 0) {
            op_type[oc] = 0;
            op_val[oc] = a[x - 1];
            oc++;
            x--;
            y--;
        }

        total_edits += found_d;
        int64_t sh = found_d;
        for (int j = 0; j < oc; j++) {
            sh = (sh * 131LL + op_type[j] * 67LL + op_val[j]) % MOD_V;
        }
        ck = (ck * 31LL + sh) % MOD_V;
    }

    printf("%" PRId64 "\n%" PRId64 "\n", total_edits, ck);
    free(v);
    free(trace);
    return 0;
}
