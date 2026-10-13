#include <stdio.h>
#include <stdint.h>

int main(void) {
    int64_t s = 0;
    int64_t i = 0;
    while (i < 50000000) {
        s += i & 1023;
        i += 1;
    }
    printf("%lld\n", (long long)s);
    return 0;
}
