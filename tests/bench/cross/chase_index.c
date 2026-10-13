#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

int main(void) {
    const int64_t n = 65536;
    int64_t *nxt = (int64_t *)malloc((size_t)n * sizeof(int64_t));
    if (!nxt) {
        return 1;
    }
    int64_t i = 0;
    while (i < n) {
        nxt[i] = ((i * 7) + 1) & (n - 1);
        i += 1;
    }
    int64_t k = 0;
    int64_t s = 0;
    while (s < 20000000) {
        k = nxt[k];
        s += 1;
    }
    printf("%lld\n", (long long)k);
    free(nxt);
    return 0;
}
