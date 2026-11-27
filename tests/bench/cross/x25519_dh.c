#include <stdint.h>
#include <stdio.h>
#include <string.h>

static void car25519(int64_t *o) {
    for (int i = 0; i < 16; i++) {
        int64_t c = o[i] >> 16;
        o[i] &= 65535LL;
        if (i < 15) {
            o[i + 1] += c;
        } else {
            o[0] += c * 38LL;
        }
    }
}

static void fadd(int64_t *o, const int64_t *a, const int64_t *b) {
    for (int i = 0; i < 16; i++) {
        o[i] = a[i] + b[i];
    }
}

static void fsub(int64_t *o, const int64_t *a, const int64_t *b) {
    o[0] = a[0] + 130996LL - b[0];
    for (int i = 1; i < 16; i++) {
        o[i] = a[i] + 131070LL - b[i];
    }
    car25519(o);
}

static void fmul(int64_t *o, const int64_t *a, const int64_t *b) {
    int64_t t[32];
    for (int i = 0; i < 32; i++) t[i] = 0;
    for (int i = 0; i < 16; i++) {
        int64_t ai = a[i];
        for (int j = 0; j < 16; j++) {
            t[i + j] += ai * b[j];
        }
    }
    for (int i = 0; i < 16; i++) {
        o[i] = t[i] + 38LL * t[i + 16];
    }
    car25519(o);
    car25519(o);
}

static void cswap(int64_t *p, int64_t *q, int64_t bit) {
    if (bit != 0) {
        for (int i = 0; i < 16; i++) {
            int64_t tmp = p[i];
            p[i] = q[i];
            q[i] = tmp;
        }
    }
}

static void finv(int64_t *o, const int64_t *in_v) {
    int64_t c[16];
    memcpy(c, in_v, sizeof(c));
    for (int a = 253; a >= 0; a--) {
        fmul(c, c, c);
        if (a != 2 && a != 4) {
            fmul(c, c, in_v);
        }
    }
    memcpy(o, c, sizeof(c));
}

static void pack25519(int64_t *o, const int64_t *n_in) {
    int64_t t[16], m[16];
    memcpy(t, n_in, sizeof(t));
    car25519(t);
    car25519(t);
    car25519(t);
    for (int pass = 0; pass < 2; pass++) {
        m[0] = t[0] - 65517LL;
        int64_t borrow = 0;
        if (m[0] < 0) {
            m[0] += 65536LL;
            borrow = 1;
        }
        for (int i = 1; i < 15; i++) {
            m[i] = t[i] - 65535LL - borrow;
            if (m[i] < 0) {
                m[i] += 65536LL;
                borrow = 1;
            } else {
                borrow = 0;
            }
        }
        m[15] = t[15] - 32767LL - borrow;
        if (m[15] >= 0) {
            memcpy(t, m, sizeof(t));
        }
    }
    for (int i = 0; i < 16; i++) {
        o[2 * i] = t[i] & 255LL;
        o[2 * i + 1] = (t[i] >> 8) & 255LL;
    }
}

static void x25519(int64_t *q, const int64_t *n_bytes, const int64_t *p_bytes, const int64_t *a24) {
    int64_t z[32];
    memcpy(z, n_bytes, sizeof(z));
    z[0] &= 248LL;
    z[31] = (z[31] & 127LL) | 64LL;

    int64_t x[16], a[16], b[16], c[16], d[16], e[16], f[16];
    for (int i = 0; i < 16; i++) {
        x[i] = p_bytes[2 * i] | (p_bytes[2 * i + 1] << 8);
        a[i] = 0;
        c[i] = 0;
        d[i] = 0;
    }
    x[15] &= 32767LL;
    a[0] = 1;
    memcpy(b, x, sizeof(b));
    d[0] = 1;

    for (int bit_i = 254; bit_i >= 0; bit_i--) {
        int64_t r = (z[bit_i >> 3] >> (bit_i & 7)) & 1LL;
        cswap(a, b, r);
        cswap(c, d, r);
        fadd(e, a, c);
        fsub(a, a, c);
        fadd(c, b, d);
        fsub(b, b, d);
        fmul(d, e, e);
        fmul(f, a, a);
        fmul(a, c, a);
        fmul(c, b, e);
        fadd(e, a, c);
        fsub(a, a, c);
        fmul(b, a, a);
        fsub(c, d, f);
        fmul(a, c, a24);
        fadd(a, a, d);
        fmul(c, c, a);
        fmul(a, d, f);
        fmul(d, b, x);
        fmul(b, e, e);
        cswap(a, b, r);
        cswap(c, d, r);
    }
    memcpy(e, c, sizeof(e));
    finv(c, e);
    fmul(a, a, c);
    pack25519(q, a);
}

int main(void) {
    int64_t a24[16] = {56129LL, 1LL, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    int64_t k[32], u[32], out[32];
    for (int i = 0; i < 32; i++) {
        k[i] = 0;
        u[i] = 0;
    }
    k[0] = 9;
    u[0] = 9;

    for (int step = 0; step < 100; step++) {
        x25519(out, k, u, a24);
        memcpy(u, k, sizeof(u));
        memcpy(k, out, sizeof(k));
    }

    printf("100\n");
    for (int i = 0; i < 32; i++) {
        printf("%02x", (unsigned)k[i]);
    }
    printf("\n");
    return 0;
}
