#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

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
    double *g = (double *)malloc((size_t)(n * n) * sizeof(double));
    if (!g) return 1;
    for (int i = 0; i < n * n; i++) {
        g[i] = next_double(&rng);
    }

    const double omega = 1.25;
    const double omega_over_four = omega * 0.25;
    const double one_minus_omega = 1.0 - omega;
    for (int p = 0; p < 500; p++) {
        for (int i = 1; i < n - 1; i++) {
            int row = i * n;
            int up = (i - 1) * n;
            int dn = (i + 1) * n;
            for (int j = 1; j < n - 1; j++) {
                g[row + j] = omega_over_four * (g[up + j] + g[dn + j] + g[row + j - 1] + g[row + j + 1]) + one_minus_omega * g[row + j];
            }
        }
    }

    double total = 0.0;
    for (int i = 0; i < n * n; i++) {
        total += g[i];
    }
    printf("%lld\n", (long long)floor(total * 1000.0 + 0.5));
    free(g);
    return 0;
}
