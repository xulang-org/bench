#include <stdint.h>
#include <stdio.h>

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
    SciRandom rng;
    init_random(&rng, 113);
    int64_t under = 0;
    for (int i = 0; i < 5000000; i++) {
        double x = next_double(&rng);
        double y = next_double(&rng);
        if (x * x + y * y <= 1.0) {
            under++;
        }
    }
    printf("%lld\n", (long long)under);
    return 0;
}
