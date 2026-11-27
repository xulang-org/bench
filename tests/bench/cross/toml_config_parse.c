#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MOD_V 1000000007LL

typedef struct {
    int64_t *data;
    int len;
    int cap;
} Vec64;

static void vec_init(Vec64 *v, int cap) {
    v->data = (int64_t *)malloc((size_t)cap * sizeof(int64_t));
    v->len = 0;
    v->cap = cap;
}

static void vec_push(Vec64 *v, int64_t x) {
    if (v->len == v->cap) {
        v->cap *= 2;
        v->data = (int64_t *)realloc(v->data, (size_t)v->cap * sizeof(int64_t));
    }
    v->data[v->len++] = x;
}

static void push_str(Vec64 *v, const char *s) {
    while (*s) {
        vec_push(v, (int64_t)(unsigned char)(*s));
        s++;
    }
}

static void push_int(Vec64 *v, int64_t x) {
    if (x < 0) { vec_push(v, 45); x = -x; }
    if (x == 0) { vec_push(v, 48); return; }
    int64_t digs[16];
    int dc = 0;
    while (x > 0) { digs[dc++] = 48 + (x % 10); x /= 10; }
    for (int i = dc - 1; i >= 0; i--) vec_push(v, digs[i]);
}

static void push_2d(Vec64 *v, int64_t x) {
    vec_push(v, 48 + (x / 10));
    vec_push(v, 48 + (x % 10));
}

typedef struct {
    int64_t val;
    int nextp;
} ValRes;

static ValRes parse_val(const int64_t *doc, int p, int n) {
    if (doc[p] == 34) {
        p++;
        int64_t vh = 17;
        while (p < n && doc[p] != 34) {
            int64_t ch = doc[p];
            if (ch == 92 && p + 1 < n) {
                p++;
                int64_t e = doc[p];
                if (e == 110) ch = 10;
                else if (e == 116) ch = 9;
                else if (e == 34) ch = 34;
                else if (e == 92) ch = 92;
                else ch = e;
            }
            vh = (vh * 131 + ch) % MOD_V;
            p++;
        }
        if (p < n) p++;
        ValRes r = {vh, p};
        return r;
    } else if (doc[p] == 91) {
        p++;
        int64_t ah = 29;
        while (p < n) {
            while (p < n && (doc[p] == 32 || doc[p] == 9 || doc[p] == 44)) p++;
            if (p >= n || doc[p] == 93) {
                if (p < n) p++;
                break;
            }
            ValRes sub = parse_val(doc, p, n);
            ah = (ah * 257 + sub.val) % MOD_V;
            p = sub.nextp;
        }
        ValRes r = {ah, p};
        return r;
    } else if (doc[p] == 116) {
        ValRes r = {1, p + 4};
        return r;
    } else if (doc[p] == 102) {
        ValRes r = {0, p + 5};
        return r;
    }
    int neg = 0;
    if (doc[p] == 45) { neg = 1; p++; }
    int64_t v = 0;
    while (p < n && ((doc[p] >= 48 && doc[p] <= 57) || doc[p] == 95)) {
        if (doc[p] != 95) v = v * 10 + (doc[p] - 48);
        p++;
    }
    if (neg) v = -v;
    v %= MOD_V;
    if (v < 0) v += MOD_V;
    ValRes r = {v, p};
    return r;
}

int main(void) {
    Vec64 dv;
    vec_init(&dv, 16384);
    push_str(&dv, "# Auto-generated microservice configuration\n");
    for (int64_t s = 0; s < 48; s++) {
        push_str(&dv, "\n[svc_"); push_2d(&dv, s); push_str(&dv, "]\n");
        push_str(&dv, "name = \"worker-"); push_2d(&dv, s);
        push_str(&dv, "\\tprod\\n\\\"v"); push_int(&dv, s % 5);
        push_str(&dv, "\\\"\" # inline comment\n");
        push_str(&dv, "port = "); push_int(&dv, 8000 + s * 10); vec_push(&dv, 10);
        push_str(&dv, "max_conn = "); push_int(&dv, 1000 + (s % 7) * 500);
        vec_push(&dv, 95); push_int(&dv, 100 + s); vec_push(&dv, 10);
        if ((s & 1) == 0) push_str(&dv, "enabled = true\n");
        else push_str(&dv, "enabled = false\n");
        if ((s % 9) == 0) { push_str(&dv, "timeout_ms = -"); push_int(&dv, 50 + s * 3); vec_push(&dv, 10); }
        else { push_str(&dv, "timeout_ms = "); push_int(&dv, 250 + s * 15); vec_push(&dv, 10); }
        push_str(&dv, "retries = [");
        push_int(&dv, 1 + (s % 3)); push_str(&dv, ", ");
        push_int(&dv, 2 + (s % 5)); push_str(&dv, ", ");
        push_int(&dv, 4 + (s % 7)); push_str(&dv, ", ");
        push_int(&dv, 8 + (s % 11)); push_str(&dv, "]\n");
        push_str(&dv, "endpoints = [\"/v1/s"); push_int(&dv, s);
        push_str(&dv, "\", \"/health\\t"); push_int(&dv, s);
        push_str(&dv, "\", \"/metrics\"]\n");
    }

    const int64_t *doc = dv.data;
    int n = dv.len;
    int64_t total_entries = 0, ck = 0;
    for (int64_t rnd = 0; rnd < 1000; rnd++) {
        int pos = 0;
        int64_t sec_hash = 0, entries = 0, round_ck = 0;
        while (pos < n) {
            while (pos < n && (doc[pos] == 32 || doc[pos] == 9 || doc[pos] == 10 || doc[pos] == 13)) pos++;
            if (pos >= n) break;
            int64_t c = doc[pos];
            if (c == 35) { while (pos < n && doc[pos] != 10) pos++; continue; }
            if (c == 91) {
                pos++;
                int64_t sh = 0;
                while (pos < n && doc[pos] != 93) { sh = (sh * 131 + doc[pos]) % MOD_V; pos++; }
                if (pos < n) pos++;
                sec_hash = sh;
                while (pos < n && doc[pos] != 10) pos++;
                continue;
            }
            int64_t kh = sec_hash;
            while (pos < n && doc[pos] != 61 && doc[pos] != 32 && doc[pos] != 9 && doc[pos] != 10) {
                kh = (kh * 131 + doc[pos]) % MOD_V;
                pos++;
            }
            while (pos < n && (doc[pos] == 32 || doc[pos] == 9)) pos++;
            if (pos < n && doc[pos] == 61) pos++;
            while (pos < n && (doc[pos] == 32 || doc[pos] == 9)) pos++;
            ValRes res = parse_val(doc, pos, n);
            pos = res.nextp;
            while (pos < n && doc[pos] != 10) pos++;
            entries++;
            round_ck = (round_ck * 31 + (kh * 7 + res.val + rnd) % MOD_V) % MOD_V;
        }
        total_entries += entries;
        ck = (ck * 37 + round_ck) % MOD_V;
    }
    free(dv.data);
    printf("%" PRId64 "\n%" PRId64 "\n", total_entries, ck);
    return 0;
}
