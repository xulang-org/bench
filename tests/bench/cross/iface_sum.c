#include <stdint.h>
#include <stdio.h>

typedef struct A {
    int64_t x;
} A;

typedef struct B {
    int64_t x;
} B;

typedef struct Src {
    int64_t (*val)(const void *);
    const void *p;
} Src;

static int64_t val_a(const void *p) {
    return ((const A *)p)->x;
}

static int64_t val_b(const void *p) {
    return ((const B *)p)->x * 2;
}

int main(void) {
    A a = {1};
    B b = {2};
    Src xs[2];
    xs[0].val = val_a;
    xs[0].p = &a;
    xs[1].val = val_b;
    xs[1].p = &b;
    int64_t s = 0;
    int64_t i = 0;
    while (i < 8000000) {
        Src *e = &xs[i & 1];
        s += e->val(e->p);
        i += 1;
    }
    printf("%lld\n", (long long)s);
    return 0;
}
