#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MOD_V 1000000007LL

typedef struct {
    int64_t *data;
    int len;
    int cap;
} Vec64;

static Vec64 to_bytes(const char *s) {
    int n = (int)strlen(s);
    Vec64 v;
    v.data = (int64_t *)malloc((size_t)(n > 0 ? n : 1) * sizeof(int64_t));
    v.len = n;
    v.cap = n > 0 ? n : 1;
    for (int i = 0; i < n; i++) v.data[i] = (int64_t)(unsigned char)s[i];
    return v;
}

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

static void emit_raw(Vec64 *out, const int64_t *s, int start, int ln) {
    for (int i = 0; i < ln; i++) vec_push(out, s[start + i]);
}

static void emit_esc(Vec64 *out, const Vec64 *s) {
    const int64_t *sd = s->data;
    int n = s->len;
    for (int i = 0; i < n; i++) {
        int64_t ch = sd[i];
        if (ch == 38) { vec_push(out, 38); vec_push(out, 97); vec_push(out, 109); vec_push(out, 112); vec_push(out, 59); }
        else if (ch == 60) { vec_push(out, 38); vec_push(out, 108); vec_push(out, 116); vec_push(out, 59); }
        else if (ch == 62) { vec_push(out, 38); vec_push(out, 103); vec_push(out, 116); vec_push(out, 59); }
        else if (ch == 34) { vec_push(out, 38); vec_push(out, 113); vec_push(out, 117); vec_push(out, 111); vec_push(out, 116); vec_push(out, 59); }
        else if (ch == 39) { vec_push(out, 38); vec_push(out, 35); vec_push(out, 51); vec_push(out, 57); vec_push(out, 59); }
        else vec_push(out, ch);
    }
}

static int match_bytes(const int64_t *src, int s, int e, const char *pat) {
    int a = s, b = e;
    while (a < b && (src[a] == 32 || src[a] == 9)) a++;
    while (b > a && (src[b - 1] == 32 || src[b - 1] == 9)) b--;
    int plen = (int)strlen(pat);
    if (b - a != plen) return 0;
    for (int i = 0; i < plen; i++) {
        if (src[a + i] != (int64_t)(unsigned char)pat[i]) return 0;
    }
    return 1;
}

static int var_id(const int64_t *src, int s, int e) {
    if (match_bytes(src, s, e, "title")) return 0;
    if (match_bytes(src, s, e, "badge")) return 1;
    if (match_bytes(src, s, e, "name")) return 2;
    if (match_bytes(src, s, e, "desc")) return 3;
    return -1;
}

int main(void) {
    Vec64 tmpl = to_bytes("<div class=\"card\"><h1>{{title}}</h1>{{{badge}}}<ul>{%for item%}<li class=\"{%if featured%}hot{%else%}std{%endif%}\"><span>{{name}}</span><em>{{desc}}</em></li>{%endfor%}</ul></div>");
    int tlen = tmpl.len;

    Vec64 titles[4] = {
        to_bytes("Xu <Fast> & Safe"), to_bytes("Bench \"Suite\" 'v1'"),
        to_bytes("Release & Notes <2026>"), to_bytes("Core / Engine"),
    };
    Vec64 badges[4] = {
        to_bytes("<b>PRO</b>"), to_bytes("<i>LTS</i>"), to_bytes("<span>NEW</span>"), to_bytes("<b>OK</b>"),
    };
    Vec64 names[8] = {
        to_bytes("Item <alpha> & 1"), to_bytes("Widget \"beta\""), to_bytes("Node 'gamma' > 0"), to_bytes("Cache & Pool"),
        to_bytes("Router <v2>"), to_bytes("Codec \"lz4\""), to_bytes("Parser 'ast'"), to_bytes("Engine <core>"),
    };
    Vec64 descs[4] = {
        to_bytes("a < b && c > d"), to_bytes("quote \"here\" & 'there'"),
        to_bytes("plain fast path"), to_bytes("x & y < z"),
    };

    int op_kind[64], op_a[64], op_b[64];
    int for_stack[8], if_stack[8], else_stack[8];
    Vec64 out;
    vec_init(&out, 2048);

    int64_t total_bytes = 0, ck = 0;
    for (int rnd = 0; rnd < 400; rnd++) {
        int n_ops = 0, for_sp = 0, if_sp = 0, pos = 0;
        while (pos < tlen) {
            int np = pos;
            while (np + 1 < tlen && !(tmpl.data[np] == 123 && (tmpl.data[np + 1] == 123 || tmpl.data[np + 1] == 37))) np++;
            if (np + 1 >= tlen) np = tlen;
            if (np > pos) {
                op_kind[n_ops] = 0; op_a[n_ops] = pos; op_b[n_ops] = np - pos; n_ops++;
                pos = np;
            }
            if (pos >= tlen) break;
            if (tmpl.data[pos + 1] == 123) {
                if (pos + 2 < tlen && tmpl.data[pos + 2] == 123) {
                    int end = pos + 3;
                    while (!(tmpl.data[end] == 125 && tmpl.data[end + 1] == 125 && tmpl.data[end + 2] == 125)) end++;
                    op_kind[n_ops] = 2; op_a[n_ops] = var_id(tmpl.data, pos + 3, end); op_b[n_ops] = 0; n_ops++;
                    pos = end + 3;
                } else {
                    int end = pos + 2;
                    while (!(tmpl.data[end] == 125 && tmpl.data[end + 1] == 125)) end++;
                    op_kind[n_ops] = 1; op_a[n_ops] = var_id(tmpl.data, pos + 2, end); op_b[n_ops] = 0; n_ops++;
                    pos = end + 2;
                }
            } else {
                int end = pos + 2;
                while (!(tmpl.data[end] == 37 && tmpl.data[end + 1] == 125)) end++;
                int ts = pos + 2;
                if (match_bytes(tmpl.data, ts, end, "for item")) {
                    for_stack[for_sp++] = n_ops;
                    op_kind[n_ops] = 3; op_a[n_ops] = 0; op_b[n_ops] = 0; n_ops++;
                } else if (match_bytes(tmpl.data, ts, end, "endfor")) {
                    int fidx = for_stack[--for_sp];
                    op_kind[n_ops] = 4; op_a[n_ops] = fidx + 1; op_b[n_ops] = 0; n_ops++;
                    op_a[fidx] = n_ops;
                } else if (match_bytes(tmpl.data, ts, end, "if featured")) {
                    if_stack[if_sp] = n_ops;
                    else_stack[if_sp] = -1;
                    if_sp++;
                    op_kind[n_ops] = 5; op_a[n_ops] = 0; op_b[n_ops] = 0; n_ops++;
                } else if (match_bytes(tmpl.data, ts, end, "else")) {
                    int eidx = n_ops;
                    op_kind[n_ops] = 6; op_a[n_ops] = 0; op_b[n_ops] = 0; n_ops++;
                    int iidx = if_stack[if_sp - 1];
                    op_a[iidx] = eidx + 1;
                    else_stack[if_sp - 1] = eidx;
                } else if (match_bytes(tmpl.data, ts, end, "endif")) {
                    if_sp--;
                    int iidx = if_stack[if_sp];
                    int eidx = else_stack[if_sp];
                    if (eidx >= 0) op_a[eidx] = n_ops;
                    else op_a[iidx] = n_ops;
                    op_kind[n_ops] = 7; op_a[n_ops] = 0; op_b[n_ops] = 0; n_ops++;
                }
                pos = end + 2;
            }
        }

        for (int page = 0; page < 25; page++) {
            const Vec64 *title_v = &titles[(rnd + page) & 3];
            const Vec64 *badge_v = &badges[(rnd * 3 + page) & 3];
            out.len = 0;
            int pc = 0, item_idx = 0, item_cnt = 12;
            while (pc < n_ops) {
                int op = op_kind[pc], a = op_a[pc];
                if (op == 0) { emit_raw(&out, tmpl.data, a, op_b[pc]); pc++; }
                else if (op == 1) {
                    if (a == 0) emit_esc(&out, title_v);
                    else if (a == 2) emit_esc(&out, &names[(page + item_idx + rnd) & 7]);
                    else if (a == 3) emit_esc(&out, &descs[(page * 3 + item_idx + rnd) & 3]);
                    pc++;
                } else if (op == 2) {
                    if (a == 1) emit_raw(&out, badge_v->data, 0, badge_v->len);
                    pc++;
                } else if (op == 3) {
                    if (item_cnt == 0) pc = a;
                    else { item_idx = 0; pc++; }
                } else if (op == 4) {
                    item_idx++;
                    if (item_idx < item_cnt) pc = a;
                    else pc++;
                } else if (op == 5) {
                    if (((rnd + page + item_idx) % 3) == 0) pc++;
                    else pc = a;
                } else if (op == 6) {
                    pc = a;
                } else {
                    pc++;
                }
            }
            total_bytes += out.len;
            int64_t h = 0;
            for (int oi = 0; oi < out.len; oi++) h = (h * 131 + out.data[oi]) % MOD_V;
            ck = (ck * 31 + h) % MOD_V;
        }
    }

    free(tmpl.data);
    for (int i = 0; i < 4; i++) { free(titles[i].data); free(badges[i].data); free(descs[i].data); }
    for (int i = 0; i < 8; i++) free(names[i].data);
    free(out.data);
    printf("%" PRId64 "\n%" PRId64 "\n", total_bytes, ck);
    return 0;
}
