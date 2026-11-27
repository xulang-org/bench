#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define MOD_V 1000000007LL
#define MASK30 1073741823LL
#define BASE30 1073741824LL

typedef struct {
    int tk[128];
    int64_t tv[128];
    int tlen;
    int pos;
    int code[128];
    int64_t imm[128];
    int clen;
} Compiler;

static void lex_expr(Compiler *c, const char *s) {
    c->tlen = 0;
    int i = 0;
    int n = (int)strlen(s);
    while (i < n) {
        unsigned char b = (unsigned char)s[i];
        if (b == 32) {
            i++;
        } else if (b >= 48 && b <= 57) {
            int64_t v = 0;
            while (i < n && s[i] >= 48 && s[i] <= 57) {
                v = (v * 10LL + (int64_t)(s[i] - 48)) & MASK30;
                i++;
            }
            c->tk[c->tlen] = 1;
            c->tv[c->tlen] = v;
            c->tlen++;
        } else {
            int kind = 15;
            if (b == 120) kind = 2;
            else if (b == 121) kind = 3;
            else if (b == 122) kind = 4;
            else if (b == 43) kind = 5;
            else if (b == 45) kind = 6;
            else if (b == 42) kind = 7;
            else if (b == 47) kind = 8;
            else if (b == 37) kind = 9;
            else if (b == 38) kind = 10;
            else if (b == 124) kind = 11;
            else if (b == 94) kind = 12;
            else if (b == 126) kind = 13;
            else if (b == 40) kind = 14;
            c->tk[c->tlen] = kind;
            c->tv[c->tlen] = 0;
            c->tlen++;
            i++;
        }
    }
    c->tk[c->tlen] = 0;
    c->tv[c->tlen] = 0;
    c->tlen++;
    c->pos = 0;
    c->clen = 0;
}

static void parse_or(Compiler *c);

static void emit(Compiler *c, int op, int64_t imm) {
    c->code[c->clen] = op;
    c->imm[c->clen] = imm;
    c->clen++;
}

static void parse_prim(Compiler *c) {
    int t = c->tk[c->pos];
    if (t == 1) {
        emit(c, 1, c->tv[c->pos]);
        c->pos++;
    } else if (t == 2 || t == 3 || t == 4) {
        emit(c, t, 0);
        c->pos++;
    } else {
        c->pos++;
        parse_or(c);
        c->pos++;
    }
}

static void parse_unary(Compiler *c) {
    int t = c->tk[c->pos];
    if (t == 6) {
        c->pos++;
        parse_unary(c);
        emit(c, 13, 0);
    } else if (t == 13) {
        c->pos++;
        parse_unary(c);
        emit(c, 14, 0);
    } else {
        parse_prim(c);
    }
}

static void parse_mul(Compiler *c) {
    parse_unary(c);
    while (c->tk[c->pos] == 7 || c->tk[c->pos] == 8 || c->tk[c->pos] == 9) {
        int op = c->tk[c->pos++];
        parse_unary(c);
        emit(c, op, 0);
    }
}

static void parse_add(Compiler *c) {
    parse_mul(c);
    while (c->tk[c->pos] == 5 || c->tk[c->pos] == 6) {
        int op = c->tk[c->pos++];
        parse_mul(c);
        emit(c, op, 0);
    }
}

static void parse_and(Compiler *c) {
    parse_add(c);
    while (c->tk[c->pos] == 10) {
        c->pos++;
        parse_add(c);
        emit(c, 10, 0);
    }
}

static void parse_xor(Compiler *c) {
    parse_and(c);
    while (c->tk[c->pos] == 12) {
        c->pos++;
        parse_and(c);
        emit(c, 12, 0);
    }
}

static void parse_or(Compiler *c) {
    parse_xor(c);
    while (c->tk[c->pos] == 11) {
        c->pos++;
        parse_xor(c);
        emit(c, 11, 0);
    }
}

int main(void) {
    static const char *exprs[16] = {
        "((x + y) * (z + 7) - (x ^ y)) / ((z & 15) + 1) + (x % 97)",
        "(~x & 65535) + ((y * 13 + z) ^ (x + y + z)) - (y / 3)",
        "((x * 3 + y * 5 + z * 7) ^ (x * 11 - y)) + ((z | 255) & (x + 1023))",
        "-(x - y) + (z * (x & 255) + (y % 31)) ^ (~z & 4095)",
        "(((x + 17) * (y + 29)) % 65521) + ((z ^ (x + y)) / ((x & 7) + 1))",
        "((x | y) & (y | z) & (z | x)) + ((x ^ y ^ z) * 19) - (z % 17)",
        "(x + (y + (z + (x * 3 + (y * 5 - z))))) & 1048575",
        "((x / 5 + y / 7 + z / 11) * (x % 13 + y % 17 + 1)) ^ (x + z)",
        "((~x & 1023) * (~y & 1023) + (~z & 1023)) % 1000003",
        "(((x ^ 12345) + (y ^ 6789)) * 7) / ((z % 23) + 2) + (y & 511)",
        "(x * (y & 63) - y * (z & 63) + z * (x & 63)) ^ ((x + y) | z)",
        "((x + y + z) * (x + y + z)) / (x % 29 + y % 31 + 3) + (~(x & y) & 8191)",
        "(((x & 4095) + 1) * ((y & 4095) + 3) + ((z & 4095) + 5)) ^ (x * 17)",
        "((x - (y - (z - x))) + (y * 9 - z * 5)) % 99991 + (x & z)",
        "((x | 85) ^ (y | 170) ^ (z | 51)) + ((x + y) * 23) / ((y & 31) + 1)",
        "((((x + 3) * 5 - y) ^ (z + 11)) + ((y + 7) * (z & 127))) % 524287"
    };

    Compiler comp;
    int64_t st[32];
    int64_t total_insts = 0;
    int64_t ck = 0;
    int64_t rng = 112233445LL;

    for (int rnd = 0; rnd < 160; rnd++) {
        for (int ei = 0; ei < 16; ei++) {
            lex_expr(&comp, exprs[ei]);
            parse_or(&comp);
            emit(&comp, 0, 0);

            for (int run_i = 0; run_i < 100; run_i++) {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int64_t x = rng & 65535LL;
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int64_t y = rng & 65535LL;
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int64_t z = rng & 65535LL;

                int sp = 0;
                int ip = 0;
                int64_t steps = 0;
                while (1) {
                    int op = comp.code[ip];
                    if (op == 0) {
                        break;
                    }
                    steps++;
                    if (op == 1) {
                        st[sp++] = comp.imm[ip];
                    } else if (op == 2) {
                        st[sp++] = x;
                    } else if (op == 3) {
                        st[sp++] = y;
                    } else if (op == 4) {
                        st[sp++] = z;
                    } else if (op == 5) {
                        sp--;
                        st[sp - 1] = (st[sp - 1] + st[sp]) & MASK30;
                    } else if (op == 6) {
                        sp--;
                        st[sp - 1] = (st[sp - 1] - st[sp] + BASE30) & MASK30;
                    } else if (op == 7) {
                        sp--;
                        st[sp - 1] = ((st[sp - 1] & 32767LL) * (st[sp] & 32767LL)) & MASK30;
                    } else if (op == 8) {
                        sp--;
                        st[sp - 1] = st[sp - 1] / (st[sp] + 1LL);
                    } else if (op == 9) {
                        sp--;
                        st[sp - 1] = st[sp - 1] % (st[sp] + 1LL);
                    } else if (op == 10) {
                        sp--;
                        st[sp - 1] = st[sp - 1] & st[sp];
                    } else if (op == 11) {
                        sp--;
                        st[sp - 1] = st[sp - 1] | st[sp];
                    } else if (op == 12) {
                        sp--;
                        st[sp - 1] = st[sp - 1] ^ st[sp];
                    } else if (op == 13) {
                        st[sp - 1] = (BASE30 - st[sp - 1]) & MASK30;
                    } else {
                        st[sp - 1] = st[sp - 1] ^ MASK30;
                    }
                    ip++;
                }
                total_insts += steps;
                ck = (ck * 31LL + st[sp - 1]) % MOD_V;
            }
        }
    }

    printf("%" PRId64 "\n%" PRId64 "\n", total_insts, ck);
    return 0;
}
