#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

int main(void) {
    const int64_t n = 1048576;
    int64_t *src = (int64_t *)malloc((size_t)n * sizeof(int64_t));
    int64_t *dst = (int64_t *)malloc((size_t)n * sizeof(int64_t));
    if (!src || !dst) {
        return 1;
    }
    int64_t i = 0;
    while (i < n) {
        src[i] = i & 1023;
        dst[i] = i & 1023;
        i += 1;
    }
    int64_t t = 0;
    while (t < 80) {
        i = 0;
        while (i < n) {
            dst[i] = src[i];
            i += 1;
        }
        t += 1;
    }
    int64_t s = 0;
    i = 0;
    while (i < n) {
        s += dst[i];
        i += 1;
    }
    printf("%lld\n", (long long)s);
    free(src);
    free(dst);
    return 0;
}
