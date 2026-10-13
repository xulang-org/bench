#include <stdio.h>
#include <stdint.h>

int main(void) {
    int64_t s = 0;
    int64_t i = 0;
    while (i < 8000) {
        int64_t j = 0;
        while (j < 8000) {
            s += (i * j) & 1023;
            j += 1;
        }
        i += 1;
    }
    printf("%lld\n", (long long)s);
    return 0;
}
