#include <stdio.h>
#include <stdint.h>
#include <string.h>

static int64_t tokenize(const char *src, int n, int *out_count) {
    int pos = 0;
    int count = 0;
    int64_t chk = 0;
    while (pos < n) {
        int c = (unsigned char)src[pos];
        if (c == 32 || c == 9 || c == 10 || c == 13) {
            pos++;
            continue;
        }
        int t_type = 0;
        int t_len = 0;
        if (c == 123) {
            t_type = 1; t_len = 1; pos++;
        } else if (c == 125) {
            t_type = 2; t_len = 1; pos++;
        } else if (c == 91) {
            t_type = 3; t_len = 1; pos++;
        } else if (c == 93) {
            t_type = 4; t_len = 1; pos++;
        } else if (c == 58) {
            t_type = 5; t_len = 1; pos++;
        } else if (c == 44) {
            t_type = 6; t_len = 1; pos++;
        } else if (c == 34) {
            t_type = 7;
            int start = pos;
            pos++;
            while (pos < n) {
                int ch = (unsigned char)src[pos];
                if (ch == 92) {
                    pos += 2;
                } else if (ch == 34) {
                    pos++;
                    break;
                } else {
                    pos++;
                }
            }
            t_len = pos - start;
        } else if (c == 45 || (c >= 48 && c <= 57)) {
            t_type = 8;
            int start = pos;
            if (c == 45) pos++;
            while (pos < n && ((unsigned char)src[pos] >= 48 && (unsigned char)src[pos] <= 57)) {
                pos++;
            }
            if (pos < n && (unsigned char)src[pos] == 46) {
                pos++;
                while (pos < n && ((unsigned char)src[pos] >= 48 && (unsigned char)src[pos] <= 57)) {
                    pos++;
                }
            }
            t_len = pos - start;
        } else if (c == 116) {
            t_type = 9; t_len = 4; pos += 4;
        } else if (c == 102) {
            t_type = 10; t_len = 5; pos += 5;
        } else if (c == 110) {
            t_type = 11; t_len = 4; pos += 4;
        } else {
            pos++;
            continue;
        }
        count++;
        chk = (chk * 37 + (int64_t)t_type * 101 + t_len) % 1000000007;
    }
    if (out_count) *out_count = count;
    return chk;
}

int main(void) {
    const char *base = "{\"project\":\"Xu\",\"version\":1.0,\"active\":true,\"count\":100,\"flag\":false,\"note\":null,\"data\":[1,2,-3,40]}";
    char full[1001];
    full[0] = '\0';
    for (int i = 0; i < 10; i++) {
        strcat(full, base);
    }
    int n = strlen(full);
    int count = 0;
    int64_t total = 0;
    for (int r = 0; r < 1000; r++) {
        int64_t c = tokenize(full, n, &count);
        total = (total * 31 + c) % 1000000007;
    }
    printf("%lld\n", total);
    return 0;
}
