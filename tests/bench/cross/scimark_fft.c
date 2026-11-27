#include <math.h>
#include <stdint.h>
#include <stdio.h>
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

static void fft_bitreverse(double *data, int n) {
    int j = 0;
    for (int i = 0; i < n - 1; i++) {
        if (i < j) {
            int ii = 2 * i;
            int jj = 2 * j;
            double tr = data[ii];
            double ti = data[ii + 1];
            data[ii] = data[jj];
            data[ii + 1] = data[jj + 1];
            data[jj] = tr;
            data[jj + 1] = ti;
        }
        int k = n >> 1;
        while (k <= j) {
            j -= k;
            k >>= 1;
        }
        j += k;
    }
}

static void fft_transform(double *data, int n, double direction) {
    const double pi = 3.14159265358979323846;
    fft_bitreverse(data, n);
    int dual = 1;
    for (int bit = 0; bit < 10; bit++) {
        double w_real = 1.0;
        double w_imag = 0.0;
        double theta = 2.0 * direction * pi / (2.0 * (double)dual);
        double s = sin(theta);
        double t = sin(theta * 0.5);
        double s2 = 2.0 * t * t;

        for (int b = 0; b < n; b += 2 * dual) {
            int i = 2 * b;
            int j = 2 * (b + dual);
            double wd_real = data[j];
            double wd_imag = data[j + 1];
            data[j] = data[i] - wd_real;
            data[j + 1] = data[i + 1] - wd_imag;
            data[i] += wd_real;
            data[i + 1] += wd_imag;
        }

        for (int a = 1; a < dual; a++) {
            double tmp_real = w_real - s * w_imag - s2 * w_real;
            double tmp_imag = w_imag + s * w_real - s2 * w_imag;
            w_real = tmp_real;
            w_imag = tmp_imag;
            for (int b = 0; b < n; b += 2 * dual) {
                int i = 2 * (b + a);
                int j = 2 * (b + a + dual);
                double z1_real = data[j];
                double z1_imag = data[j + 1];
                double wd_real = w_real * z1_real - w_imag * z1_imag;
                double wd_imag = w_real * z1_imag + w_imag * z1_real;
                data[j] = data[i] - wd_real;
                data[j + 1] = data[i + 1] - wd_imag;
                data[i] += wd_real;
                data[i + 1] += wd_imag;
            }
        }
        dual *= 2;
    }
}

int main(void) {
    const int n = 1024;
    SciRandom rng;
    init_random(&rng, 101010);
    double orig[2048];
    double data[2048];
    for (int i = 0; i < 2 * n; i++) {
        orig[i] = next_double(&rng);
    }

    const double norm = 1.0 / (double)n;
    double acc = 0.0;
    for (int rep = 0; rep < 200; rep++) {
        memcpy(data, orig, sizeof(orig));
        fft_transform(data, n, -1.0);
        acc += fabs(data[0]) + fabs(data[1]) + fabs(data[2 * ((rep * 7) % 512)]);
        fft_transform(data, n, 1.0);
        for (int i = 0; i < 2 * n; i++) {
            data[i] *= norm;
        }
        acc += fabs(data[2 * ((rep * 13) % 512)]);
    }
    printf("%lld\n", (long long)floor(acc * 10.0 + 0.5));
    return 0;
}
