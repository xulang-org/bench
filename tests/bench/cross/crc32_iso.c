#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main(void) {
    int64_t n = 100000;
    int64_t *data = (int64_t *)malloc(n * sizeof(int64_t));
    int64_t seed = 123456789;
    int64_t i = 0;
    while (i < n) {
        seed = (seed * 1103515245 + 12345) & 2147483647;
        data[i] = seed & 255;
        i += 1;
    }
    int64_t poly = 3988292384LL;
    int64_t mask32 = 4294967295LL;
    int64_t total = 0;
    int64_t round = 0;
    while (round < 20) {
        int64_t crc = mask32;
        int64_t k = 0;
        while (k < n) {
            int64_t b = data[k];
            crc = crc ^ b;
            int64_t bit = 0;
            while (bit < 8) {
                if ((crc & 1) != 0) {
                    crc = ((crc >> 1) & 2147483647) ^ poly;
                } else {
                    crc = (crc >> 1) & 2147483647;
                }
                bit += 1;
            }
            k += 1;
        }
        total += crc ^ mask32;
        round += 1;
    }
    printf("%lld\n", (long long)total);
    free(data);
    return 0;
}
