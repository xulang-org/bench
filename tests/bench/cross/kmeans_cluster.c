#include <inttypes.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MOD_V 1000000007LL

int main(void) {
    const int n = 8192;
    const int d = 8;
    const int k = 16;
    int64_t rng = 84848484LL;

    double gt[128];
    for (int c = 0; c < k * d; c++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        gt[c] = (double)((rng % 1000LL) - 500LL) / 16.0;
    }

    double *pts = (double *)malloc((size_t)(n * d) * sizeof(double));
    int *assign = (int *)malloc((size_t)n * sizeof(int));
    for (int i = 0; i < n; i++) {
        int g = i & 15;
        for (int dim = 0; dim < d; dim++) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            pts[i * d + dim] = gt[g * d + dim] + (double)((rng % 129LL) - 64LL) / 32.0;
        }
    }

    double cent[128], sum_c[128];
    int cnt[16];
    memcpy(cent, pts, (size_t)(k * d) * sizeof(double));
    double final_inertia = 0.0;

    for (int it = 0; it < 25; it++) {
        for (int c = 0; c < k * d; c++) {
            sum_c[c] = 0.0;
        }
        for (int c = 0; c < k; c++) {
            cnt[c] = 0;
        }
        double inertia = 0.0;
        for (int i = 0; i < n; i++) {
            int pb = i * d;
            int best_c = 0;
            double best_d = 1.0e18;
            for (int c = 0; c < k; c++) {
                int cb = c * d;
                double dist = 0.0;
                for (int dim = 0; dim < d; dim++) {
                    double diff = pts[pb + dim] - cent[cb + dim];
                    dist += diff * diff;
                }
                if (dist < best_d) {
                    best_d = dist;
                    best_c = c;
                }
            }
            assign[i] = best_c;
            cnt[best_c]++;
            inertia += best_d;
            int cb = best_c * d;
            for (int dim = 0; dim < d; dim++) {
                sum_c[cb + dim] += pts[pb + dim];
            }
        }
        for (int c = 0; c < k; c++) {
            if (cnt[c] > 0) {
                double inv = 1.0 / (double)cnt[c];
                int cb = c * d;
                for (int dim = 0; dim < d; dim++) {
                    cent[cb + dim] = sum_c[cb + dim] * inv;
                }
            }
        }
        final_inertia = inertia;
    }

    int64_t ack = 0;
    for (int i = 0; i < n; i++) {
        ack = (ack * 31LL + (int64_t)assign[i] + 1LL) % MOD_V;
    }

    printf("%" PRId64 "\n%" PRId64 "\n", ack, (int64_t)floor(final_inertia + 0.5));
    free(pts);
    free(assign);
    return 0;
}
