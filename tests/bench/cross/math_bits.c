#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>

int main(void) {
    uint64_t x = UINT64_C(0x123456789abcdef0);
    uint64_t sum = 0;
    for (uint64_t i = 0; i < 5000000; i++) {
        x = __builtin_rotateleft64(x ^ i, 13);
        unsigned lz = x ? __builtin_clzll(x) : 64;
        sum += 64 - lz;
        sum += lz;
        sum += x ? __builtin_ctzll(x) : 64;
        sum += __builtin_popcountll(x);
        x = __builtin_bswap64(x);
        sum ^= __builtin_bitreverse64(x);
    }
    printf("%" PRId64 "\n", (int64_t)sum);
    return 0;
}
