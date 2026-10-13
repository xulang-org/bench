#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    size_t cap = 16;
    size_t n = 0;
    char *s = (char *)malloc(cap);
    if (!s) {
        return 1;
    }
    int64_t i = 0;
    while (i < 100000) {
        if (n + 10 + 1 > cap) {
            cap *= 2;
            s = (char *)realloc(s, cap);
            if (!s) {
                return 1;
            }
        }
        memcpy(s + n, "0123456789", 10);
        n += 10;
        i += 1;
    }
    int64_t c = 0;
    size_t j = 0;
    while (j < n) {
        c += (unsigned char)s[j];
        j += 1;
    }
    printf("%lld\n", (long long)c);
    printf("%lld\n", (long long)n);
    free(s);
    return 0;
}
