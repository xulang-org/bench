#include <stdint.h>
#include <stdio.h>

static int64_t bump(int64_t x) {
    return x + 1;
}

int main(void) {
    int64_t (*f)(int64_t) = bump;
    int64_t s = 0;
    int64_t i = 0;
    while (i < 8000000) {
        s += f(i & 7);
        i += 1;
    }
    printf("%lld\n", (long long)s);
    return 0;
}
