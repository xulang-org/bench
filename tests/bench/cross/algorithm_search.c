#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static int64_t lower_bound_i64(const int64_t *a, int64_t n, int64_t v) {
    int64_t lo = 0;
    int64_t hi = n;
    while (lo < hi) {
        int64_t mid = lo + ((hi - lo) >> 1);
        if (a[mid] < v) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo;
}

int main(void) {
    const int64_t n = 131072;
    int64_t *a = (int64_t *)malloc((size_t)n * sizeof(int64_t));
    if (!a) {
        return 1;
    }
    int64_t i = 0;
    while (i < n) {
        a[i] = i * 3;
        i += 1;
    }
    int64_t total = 0;
    int64_t q = 0;
    while (q < 4000000) {
        int64_t v = ((q * 1103515245 + 12345) & 0x3FFFF) * 3;
        total += lower_bound_i64(a, n, v);
        q += 1;
    }
    printf("%lld\n", (long long)total);
    free(a);
    return 0;
}
