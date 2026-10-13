#include <stdio.h>
#include <stdint.h>

int main(void) {
    double s = 0.0;
    int64_t i = 0;
    while (i < 20000000) {
        s += (double)(i & 1023);
        i += 1;
    }
    printf("%lld\n", (long long)(int64_t)s);
    return 0;
}
