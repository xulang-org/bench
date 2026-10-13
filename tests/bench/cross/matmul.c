#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

int main(void) {
    const int64_t n = 250;
    const int64_t nn = n * n;
    int64_t *a = (int64_t *)calloc((size_t)nn, sizeof(int64_t));
    int64_t *b = (int64_t *)calloc((size_t)nn, sizeof(int64_t));
    int64_t *c = (int64_t *)calloc((size_t)nn, sizeof(int64_t));
    if (!a || !b || !c) {
        return 1;
    }
    int64_t i = 0;
    while (i < n) {
        int64_t j = 0;
        while (j < n) {
            a[i * n + j] = (i * 31 + j * 7) & 1023;
            b[i * n + j] = (i * 17 + j * 13) & 1023;
            j += 1;
        }
        i += 1;
    }
    i = 0;
    while (i < n) {
        int64_t k = 0;
        while (k < n) {
            int64_t aik = a[i * n + k];
            int64_t j = 0;
            while (j < n) {
                c[i * n + j] = c[i * n + j] + aik * b[k * n + j];
                j += 1;
            }
            k += 1;
        }
        i += 1;
    }
    int64_t s = 0;
    int64_t t = 0;
    while (t < nn) {
        s += c[t];
        t += 1;
    }
    printf("%lld\n", (long long)s);
    free(a);
    free(b);
    free(c);
    return 0;
}
