#include <stdio.h>
#include <stdint.h>

typedef struct {
    int64_t n;
} Acc;

static void acc_add(Acc *a, int64_t x) {
    a->n += x;
}

int main(void) {
    Acc a = {0};
    int64_t i = 0;
    while (i < 8000000) {
        acc_add(&a, i & 7);
        i += 1;
    }
    printf("%lld\n", (long long)a.n);
    return 0;
}
