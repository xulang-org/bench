#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

int main(void) {
    const int64_t n = 4096;
    int64_t *a = (int64_t *)malloc((size_t)n * sizeof(int64_t));
    if (!a) {
        return 1;
    }
    int64_t i = 0;
    while (i < n) {
        a[i] = i & 1023;
        i += 1;
    }
    int64_t t = 0;
    while (t < 20000) {
        i = 1;
        while (i < n) {
            a[i] = a[i] + (a[i - 1] & 1023);
            i += 1;
        }
        t += 1;
    }
    printf("%lld\n", (long long)a[n - 1]);
    free(a);
    return 0;
}
