#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

typedef struct {
    char *data;
    int64_t len;
    int64_t cap;
} StringBuilder;

static void sb_init(StringBuilder *sb) {
    sb->cap = 64;
    sb->len = 0;
    sb->data = (char *)malloc(sb->cap);
}

static void sb_write_byte(StringBuilder *sb, char b) {
    if (sb->len + 1 >= sb->cap) {
        sb->cap *= 2;
        sb->data = (char *)realloc(sb->data, sb->cap);
    }
    sb->data[sb->len++] = b;
}

int main(void) {
    StringBuilder b;
    sb_init(&b);
    int64_t i = 0;
    while (i < 100000) {
        sb_write_byte(&b, (char)(48 + (i % 10)));
        i += 1;
    }
    int64_t c = 0;
    int64_t j = 0;
    while (j < b.len) {
        c += (unsigned char)b.data[j];
        j += 1;
    }
    printf("%lld\n%lld\n", (long long)c, (long long)b.len);
    free(b.data);
    return 0;
}
