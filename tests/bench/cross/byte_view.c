#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

int main(void) {
    int64_t total_len = 100000;
    char *s = (char *)malloc(total_len + 1);
    const char *pat = "0123456789";
    int64_t i = 0;
    while (i < 10000) {
        memcpy(s + i * 10, pat, 10);
        i += 1;
    }
    s[total_len] = '\0';

    int64_t hits = 0;
    int64_t k = 0;
    while (k < 20) {
        if (memchr(s, '9', total_len) != NULL) {
            hits += 1;
        }
        if (strstr(s, "89012") != NULL) {
            hits += 1;
        }
        k += 1;
    }
    printf("%lld\n%lld\n", (long long)hits, (long long)total_len);
    free(s);
    return 0;
}
