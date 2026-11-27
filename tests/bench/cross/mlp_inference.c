#include <inttypes.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    const int d0 = 64;
    const int d1 = 128;
    const int d2 = 64;
    const int d3 = 16;
    int64_t rng = 73737373LL;

    double *w1 = (double *)malloc((size_t)(d1 * d0) * sizeof(double));
    double b1[128];
    double *w2 = (double *)malloc((size_t)(d2 * d1) * sizeof(double));
    double b2[64];
    double *w3 = (double *)malloc((size_t)(d3 * d2) * sizeof(double));
    double b3[16];

    for (int k = 0; k < d1 * d0; k++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        w1[k] = (double)((rng % 255LL) - 127LL) / 1024.0;
    }
    for (int k = 0; k < d1; k++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        b1[k] = (double)((rng % 63LL) - 31LL) / 256.0;
    }
    for (int k = 0; k < d2 * d1; k++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        w2[k] = (double)((rng % 255LL) - 127LL) / 1024.0;
    }
    for (int k = 0; k < d2; k++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        b2[k] = (double)((rng % 63LL) - 31LL) / 256.0;
    }
    for (int k = 0; k < d3 * d2; k++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        w3[k] = (double)((rng % 255LL) - 127LL) / 1024.0;
    }
    for (int k = 0; k < d3; k++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        b3[k] = (double)((rng % 63LL) - 31LL) / 256.0;
    }

    double x[64], h1[128], h2[64];
    int64_t cls_sum = 0;
    double logit_acc = 0.0;

    for (int smp = 0; smp < 2000; smp++) {
        for (int i = 0; i < d0; i++) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            x[i] = (double)((rng % 255LL) - 127LL) / 128.0;
        }
        for (int j = 0; j < d1; j++) {
            double s = b1[j];
            int base = j * d0;
            for (int i = 0; i < d0; i++) {
                s += x[i] * w1[base + i];
            }
            h1[j] = (s > 0.0) ? s : 0.0;
        }
        for (int j = 0; j < d2; j++) {
            double s = b2[j];
            int base = j * d1;
            for (int i = 0; i < d1; i++) {
                s += h1[i] * w2[base + i];
            }
            h2[j] = (s > 0.0) ? s : 0.0;
        }
        int best_c = 0;
        double best_v = -1.0e18;
        for (int j = 0; j < d3; j++) {
            double s = b3[j];
            int base = j * d2;
            for (int i = 0; i < d2; i++) {
                s += h2[i] * w3[base + i];
            }
            if (s > best_v) {
                best_v = s;
                best_c = j;
            }
        }
        cls_sum += best_c;
        logit_acc += fabs(best_v);
    }

    printf("%" PRId64 "\n%" PRId64 "\n", cls_sum, (int64_t)floor(logit_acc * 10.0 + 0.5));
    free(w1);
    free(w2);
    free(w3);
    return 0;
}
