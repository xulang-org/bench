#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <ctype.h>

int main(void) {
    const char *seed = "alpha,beta,gamma,delta;omega,phi,chi;lambda,mu,nu";
    size_t seed_len = strlen(seed);
    size_t base_len = seed_len * 384;
    char *base = (char *)malloc(base_len + 1);
    for (int i = 0; i < 384; i++) {
        memcpy(base + i * seed_len, seed, seed_len);
    }
    base[base_len] = '\0';

    int64_t total = 0;
    char *s = (char *)malloc(base_len + 1);
    char *line = (char *)malloc(base_len + 256);

    for (int i = 0; i < 2500; i++) {
        // replace 'a' with 'A'
        for (size_t k = 0; k < base_len; k++) {
            s[k] = (base[k] == 'a') ? 'A' : base[k];
        }
        s[base_len] = '\0';
        total += (int64_t)base_len;

        // split by ';'
        int part_count = 0;
        char *parts[2048];
        char *cur = s;
        while (*cur) {
            parts[part_count++] = cur;
            char *next = strchr(cur, ';');
            if (!next) break;
            *next = '\0';
            cur = next + 1;
        }
        total += part_count;

        size_t line_len = 0;
        for (int j = 0; j < part_count; j++) {
            size_t plen = strlen(parts[j]);
            total += (int64_t)plen;
            if (parts[j][0] == 'A') {
                total += 1;
            }
            // count 'a' (should be 0 since replaced by A)
            for (size_t c = 0; c < plen; c++) {
                if (parts[j][c] == 'a') total++;
            }
            if (j > 0) line[line_len++] = '|';
            memcpy(line + line_len, parts[j], plen);
            line_len += plen;
        }
        line[line_len] = '\0';
        total += (int64_t)line_len;

        // trim space & cursor read 256
        char *start = line;
        while (isspace((unsigned char)*start)) start++;
        char *end = line + line_len - 1;
        while (end > start && isspace((unsigned char)*end)) *end-- = '\0';
        size_t trimmed_len = strlen(start);

        size_t read_n = trimmed_len < 256 ? trimmed_len : 256;
        total += (int64_t)read_n;
        size_t rem = trimmed_len - read_n;
        if (rem > 0) total += (int64_t)rem;
    }

    printf("%lld\n", (long long)total);
    free(base);
    free(s);
    free(line);
    return 0;
}
