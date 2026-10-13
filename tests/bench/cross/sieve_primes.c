#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main(void) {
    int64_t n = 2000000;
    int64_t *is_prime = (int64_t *)malloc((n + 1) * sizeof(int64_t));
    int64_t i = 0;
    while (i <= n) {
        is_prime[i] = 1;
        i += 1;
    }
    is_prime[0] = 0;
    is_prime[1] = 0;
    int64_t p = 2;
    while (p * p <= n) {
        if (is_prime[p] == 1) {
            int64_t j = p * p;
            while (j <= n) {
                is_prime[j] = 0;
                j += p;
            }
        }
        p += 1;
    }
    int64_t count = 0;
    int64_t total = 0;
    int64_t k = 2;
    while (k <= n) {
        if (is_prime[k] == 1) {
            count += 1;
            total += k;
        }
        k += 1;
    }
    printf("%lld\n%lld\n", (long long)count, (long long)total);
    free(is_prime);
    return 0;
}
