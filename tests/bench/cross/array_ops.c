#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

int main(void) {
    size_t cap = 16;
    size_t n = 0;
    int64_t *a = (int64_t *)malloc(cap * sizeof(int64_t));
    if (!a) {
        return 1;
    }
    int64_t i = 0;
    while (i < 2000000) {
        if (n == cap) {
            cap *= 2;
            a = (int64_t *)realloc(a, cap * sizeof(int64_t));
            if (!a) {
                return 1;
            }
        }
        a[n] = i;
        n += 1;
        i += 1;
    }
    int64_t s = 0;
    size_t j = 0;
    while (j < n) {
        s += a[j] & 7;
        j += 1;
    }
    printf("%lld\n", (long long)s);
    free(a);
    return 0;
}
