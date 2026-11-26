#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int64_t m[17];
    int idx_i;
    int idx_j;
} SciRandom;

static void init_random(SciRandom *r, int64_t seed) {
    const int64_t m1 = 2147483647;
    const int64_t m2 = 65536;
    int64_t jseed = seed < 0 ? -seed : seed;
    if (jseed > m1) jseed = m1;
    if ((jseed % 2) == 0) jseed--;
    const int64_t k0 = 9069 % m2;
    const int64_t k1 = 9069 / m2;
    int64_t j0 = jseed % m2;
    int64_t j1 = jseed / m2;
    for (int iloop = 0; iloop < 17; iloop++) {
        jseed = j0 * k0;
        j1 = (jseed / m2 + j0 * k1 + j1 * k0) % (m2 / 2);
        j0 = jseed % m2;
        r->m[iloop] = j0 + m2 * j1;
    }
    r->idx_i = 4;
    r->idx_j = 16;
}

static inline double next_double(SciRandom *r) {
    const int64_t m1 = 2147483647;
    const double dm1 = 1.0 / 2147483647.0;
    int64_t k = r->m[r->idx_i] - r->m[r->idx_j];
    if (k < 0) k += m1;
    r->m[r->idx_j] = k;
    r->idx_i = (r->idx_i == 0) ? 16 : (r->idx_i - 1);
    r->idx_j = (r->idx_j == 0) ? 16 : (r->idx_j - 1);
    return dm1 * (double)k;
}

int main(void) {
    const int n = 100;
    SciRandom rng;
    init_random(&rng, 101010);
    double *a0 = (double *)malloc((size_t)(n * n) * sizeof(double));
    double *a = (double *)malloc((size_t)(n * n) * sizeof(double));
    int64_t piv[100];
    if (!a0 || !a) return 1;
    for (int i = 0; i < n * n; i++) {
        a0[i] = next_double(&rng);
    }

    double lu_acc = 0.0;
    int64_t piv_chk = 0;
    for (int rep = 0; rep < 30; rep++) {
        memcpy(a, a0, (size_t)(n * n) * sizeof(double));
        for (int j = 0; j < n; j++) {
            int jp = j;
            double t = fabs(a[j * n + j]);
            for (int i = j + 1; i < n; i++) {
                double ab = fabs(a[i * n + j]);
                if (ab > t) {
                    jp = i;
                    t = ab;
                }
            }
            piv[j] = jp;
            if (jp != j) {
                for (int k = 0; k < n; k++) {
                    double tmp = a[j * n + k];
                    a[j * n + k] = a[jp * n + k];
                    a[jp * n + k] = tmp;
                }
            }
            if (j < n - 1) {
                double recp = 1.0 / a[j * n + j];
                for (int k = j + 1; k < n; k++) {
                    a[k * n + j] *= recp;
                }
                for (int ii = j + 1; ii < n; ii++) {
                    double aii = a[ii * n + j];
                    for (int jj = j + 1; jj < n; jj++) {
                        a[ii * n + jj] -= aii * a[j * n + jj];
                    }
                }
            }
        }
        for (int i = 0; i < n * n; i++) {
            lu_acc += fabs(a[i]);
        }
        int64_t ps = 0;
        for (int i = 0; i < n; i++) {
            ps += piv[i];
        }
        piv_chk = (piv_chk + ps) % 1000000007;
    }
    int64_t ans = (int64_t)floor(lu_acc * 100.0 + 0.5) + piv_chk;
    printf("%lld\n", (long long)ans);
    free(a0);
    free(a);
    return 0;
}
