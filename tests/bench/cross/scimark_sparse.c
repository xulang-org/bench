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
    const int n = 10000;
    const int nz = 50000;
    const int nr = 5;
    SciRandom rng;
    init_random(&rng, 101010);

    double *x = (double *)malloc((size_t)n * sizeof(double));
    double *y = (double *)calloc((size_t)n, sizeof(double));
    double *val = (double *)malloc((size_t)nz * sizeof(double));
    int *col = (int *)malloc((size_t)nz * sizeof(int));
    int *row = (int *)calloc((size_t)(n + 1), sizeof(int));
    if (!x || !y || !val || !col || !row) return 1;

    for (int i = 0; i < n; i++) {
        x[i] = next_double(&rng);
    }
    for (int i = 0; i < nz; i++) {
        val[i] = next_double(&rng);
    }
    for (int r = 0; r < n; r++) {
        int row_r = row[r];
        row[r + 1] = row_r + nr;
        int step = r / nr;
        if (step < 1) step = 1;
        for (int j = 0; j < nr; j++) {
            col[row_r + j] = (j * step) % n;
        }
    }

    double acc = 0.0;
    for (int rep = 0; rep < 500; rep++) {
        for (int r = 0; r < n; r++) {
            double s = 0.0;
            int end = row[r + 1];
            for (int ii = row[r]; ii < end; ii++) {
                s += x[col[ii]] * val[ii];
            }
            y[r] = s;
        }
        acc += y[rep % n];
    }

    double total = acc;
    for (int i = 0; i < n; i++) {
        total += y[i];
    }
    printf("%lld\n", (long long)floor(total * 1000.0 + 0.5));
    free(x);
    free(y);
    free(val);
    free(col);
    free(row);
    return 0;
}
