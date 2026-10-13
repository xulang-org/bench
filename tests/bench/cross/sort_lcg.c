#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

static int cmp_i64(const void *pa, const void *pb) {
    int64_t x = *(const int64_t *)pa;
    int64_t y = *(const int64_t *)pb;
    return (x > y) - (x < y);
}

int main(void) {
    int64_t *a = (int64_t *)malloc(100000 * sizeof(int64_t));
    if (!a) {
        return 1;
    }
    int64_t i = 0;
    int64_t x = 12345;
    while (i < 100000) {
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF;
        a[i] = x;
        i += 1;
    }
    qsort(a, 100000, sizeof(int64_t), cmp_i64);
    printf("%lld\n", (long long)(a[0] + a[50000] * 2 + a[99999] * 3));
    free(a);
    return 0;
}
