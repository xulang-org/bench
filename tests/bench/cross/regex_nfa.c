#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int64_t *data;
    int64_t len;
    int64_t cap;
} IntVec;

static void iv_init(IntVec *v, int64_t cap) {
    v->len = 0;
    v->cap = cap > 0 ? cap : 16;
    v->data = (int64_t *)malloc((size_t)v->cap * sizeof(int64_t));
}

static void iv_push(IntVec *v, int64_t x) {
    if (v->len == v->cap) {
        v->cap *= 2;
        v->data = (int64_t *)realloc(v->data, (size_t)v->cap * sizeof(int64_t));
    }
    v->data[v->len++] = x;
}

static void iv_free(IntVec *v) {
    free(v->data);
}

typedef struct {
    IntVec st_kind;
    IntVec st_out1;
    IntVec st_out2;
    IntVec p_st;
    IntVec p_wh;
    IntVec p_next;
    int64_t start_st[6];
    int64_t match_st[6];
    int64_t num_pats;
} NfaPool;

static int64_t prec(int64_t op) {
    if (op == -3) return 1;
    if (op == -2) return 2;
    if (op == -4 || op == -5 || op == -6) return 3;
    return 0;
}

static int64_t add_st(NfaPool *nfa, int64_t k, int64_t o1, int64_t o2) {
    int64_t idx = nfa->st_kind.len;
    iv_push(&nfa->st_kind, k);
    iv_push(&nfa->st_out1, o1);
    iv_push(&nfa->st_out2, o2);
    return idx;
}

static int64_t new_patch(NfaPool *nfa, int64_t si, int64_t wh) {
    int64_t idx = nfa->p_st.len;
    iv_push(&nfa->p_st, si);
    iv_push(&nfa->p_wh, wh);
    iv_push(&nfa->p_next, -1);
    return idx;
}

static int64_t append_patch(NfaPool *nfa, int64_t h1, int64_t t1, int64_t h2) {
    if (h1 == -1) return h2;
    if (h2 == -1) return h1;
    nfa->p_next.data[t1] = h2;
    return h1;
}

static void apply_patch(NfaPool *nfa, int64_t head, int64_t target) {
    int64_t cur = head;
    while (cur != -1) {
        if (nfa->p_wh.data[cur] == 1) {
            nfa->st_out1.data[nfa->p_st.data[cur]] = target;
        } else {
            nfa->st_out2.data[nfa->p_st.data[cur]] = target;
        }
        cur = nfa->p_next.data[cur];
    }
}

static void compile_pattern(NfaPool *nfa, const char *pat) {
    int64_t toks[256];
    int64_t toks_len = 0;
    int prev_atom = 0;
    for (int64_t i = 0; pat[i] != '\0'; i++) {
        int64_t c = (int64_t)(unsigned char)pat[i];
        if (c == 40) {
            if (prev_atom) toks[toks_len++] = -2;
            toks[toks_len++] = -10;
            prev_atom = 0;
        } else if (c == 41) {
            toks[toks_len++] = -11;
            prev_atom = 1;
        } else if (c == 124) {
            toks[toks_len++] = -3;
            prev_atom = 0;
        } else if (c == 42) {
            toks[toks_len++] = -4;
            prev_atom = 1;
        } else if (c == 43) {
            toks[toks_len++] = -5;
            prev_atom = 1;
        } else if (c == 63) {
            toks[toks_len++] = -6;
            prev_atom = 1;
        } else {
            if (prev_atom) toks[toks_len++] = -2;
            toks[toks_len++] = (c == 46) ? -1 : c;
            prev_atom = 1;
        }
    }

    int64_t post[256];
    int64_t post_len = 0;
    int64_t ops[256];
    int64_t ops_len = 0;
    for (int64_t i = 0; i < toks_len; i++) {
        int64_t t = toks[i];
        if (t >= 0 || t == -1) {
            post[post_len++] = t;
        } else if (t == -10) {
            ops[ops_len++] = t;
        } else if (t == -11) {
            while (ops_len > 0 && ops[ops_len - 1] != -10) {
                post[post_len++] = ops[--ops_len];
            }
            if (ops_len > 0) ops_len--;
        } else {
            int64_t pt = prec(t);
            while (ops_len > 0 && ops[ops_len - 1] != -10 && prec(ops[ops_len - 1]) >= pt) {
                post[post_len++] = ops[--ops_len];
            }
            ops[ops_len++] = t;
        }
    }
    while (ops_len > 0) {
        post[post_len++] = ops[--ops_len];
    }

    int64_t fs[256], fh[256], ft[256];
    int64_t fsp = 0;
    for (int64_t i = 0; i < post_len; i++) {
        int64_t t = post[i];
        if (t >= 0 || t == -1) {
            int64_t s = add_st(nfa, t, -1, -1);
            int64_t p = new_patch(nfa, s, 1);
            fs[fsp] = s; fh[fsp] = p; ft[fsp] = p; fsp++;
        } else if (t == -2) {
            fsp--;
            int64_t s2 = fs[fsp], h2 = fh[fsp], t2 = ft[fsp];
            fsp--;
            int64_t s1 = fs[fsp], h1 = fh[fsp];
            apply_patch(nfa, h1, s2);
            fs[fsp] = s1; fh[fsp] = h2; ft[fsp] = t2; fsp++;
        } else if (t == -3) {
            fsp--;
            int64_t s2 = fs[fsp], h2 = fh[fsp], t2 = ft[fsp];
            fsp--;
            int64_t s1 = fs[fsp], h1 = fh[fsp], t1 = ft[fsp];
            int64_t s = add_st(nfa, -2, s1, s2);
            int64_t hn = append_patch(nfa, h1, t1, h2);
            fs[fsp] = s; fh[fsp] = hn; ft[fsp] = t2; fsp++;
        } else if (t == -6) {
            fsp--;
            int64_t s1 = fs[fsp], h1 = fh[fsp], t1 = ft[fsp];
            int64_t s = add_st(nfa, -2, s1, -1);
            int64_t p = new_patch(nfa, s, 2);
            int64_t hn = append_patch(nfa, h1, t1, p);
            fs[fsp] = s; fh[fsp] = hn; ft[fsp] = p; fsp++;
        } else if (t == -4) {
            fsp--;
            int64_t s1 = fs[fsp], h1 = fh[fsp];
            int64_t s = add_st(nfa, -2, s1, -1);
            apply_patch(nfa, h1, s);
            int64_t p = new_patch(nfa, s, 2);
            fs[fsp] = s; fh[fsp] = p; ft[fsp] = p; fsp++;
        } else if (t == -5) {
            fsp--;
            int64_t s1 = fs[fsp], h1 = fh[fsp];
            int64_t s = add_st(nfa, -2, s1, -1);
            apply_patch(nfa, h1, s);
            int64_t p = new_patch(nfa, s, 2);
            fs[fsp] = s1; fh[fsp] = p; ft[fsp] = p; fsp++;
        }
    }
    int64_t m = add_st(nfa, -3, -1, -1);
    apply_patch(nfa, fh[fsp - 1], m);
    nfa->start_st[nfa->num_pats] = fs[fsp - 1];
    nfa->match_st[nfa->num_pats] = m;
    nfa->num_pats += 1;
}

static void add_state(
    const NfaPool *nfa,
    int64_t *vis,
    int64_t *lst,
    int64_t *lst_len,
    int64_t *stk,
    int64_t s,
    int64_t gen
) {
    int64_t sp = 0;
    stk[sp++] = s;
    while (sp > 0) {
        int64_t u = stk[--sp];
        if (u < 0 || vis[u] == gen) {
            continue;
        }
        vis[u] = gen;
        if (nfa->st_kind.data[u] == -2) {
            stk[sp++] = nfa->st_out2.data[u];
            stk[sp++] = nfa->st_out1.data[u];
        } else {
            lst[(*lst_len)++] = u;
        }
    }
}

static int nfa_search(
    const NfaPool *nfa,
    int64_t start,
    int64_t match_st,
    const int64_t *text,
    int64_t tlen,
    int64_t *vis,
    int64_t *gen_box,
    int64_t *cur,
    int64_t *nxt,
    int64_t *stk
) {
    int64_t gen = *gen_box + 1;
    int64_t cur_len = 0;
    add_state(nfa, vis, cur, &cur_len, stk, start, gen);
    if (vis[match_st] == gen) {
        *gen_box = gen;
        return 1;
    }
    for (int64_t i = 0; i < tlen; i++) {
        int64_t c = text[i];
        gen += 1;
        int64_t nxt_len = 0;
        for (int64_t j = 0; j < cur_len; j++) {
            int64_t u = cur[j];
            int64_t k = nfa->st_kind.data[u];
            if (k == c || k == -1) {
                add_state(nfa, vis, nxt, &nxt_len, stk, nfa->st_out1.data[u], gen);
            }
        }
        add_state(nfa, vis, nxt, &nxt_len, stk, start, gen);
        if (vis[match_st] == gen) {
            *gen_box = gen;
            return 1;
        }
        for (int64_t k = 0; k < nxt_len; k++) {
            cur[k] = nxt[k];
        }
        cur_len = nxt_len;
    }
    *gen_box = gen;
    return 0;
}

int main(void) {
    NfaPool nfa;
    iv_init(&nfa.st_kind, 256);
    iv_init(&nfa.st_out1, 256);
    iv_init(&nfa.st_out2, 256);
    iv_init(&nfa.p_st, 256);
    iv_init(&nfa.p_wh, 256);
    iv_init(&nfa.p_next, 256);
    nfa.num_pats = 0;

    const char *patterns[6] = {
        "ab+c", "(a|ab)*cd", "x..y*z", "(foo|bar)+baz", "a(b|c)+d?", "k(m|n)*p+q"
    };
    for (int64_t pi = 0; pi < 6; pi++) {
        compile_pattern(&nfa, patterns[pi]);
    }

    const char *tokens[30] = {
        "ab", "bc", "cd", "foo", "bar", "baz", "xyz", "x12y", "yz", "kmpq",
        "knppq", "abc", "abbc", "abd", "acd", "a", "b", "c", "d", "x",
        "y", "z", "k", "m", "n", "p", "q", "0", "_", "-"
    };
    int64_t tok_lens[30];
    for (int64_t i = 0; i < 30; i++) {
        tok_lens[i] = (int64_t)strlen(tokens[i]);
    }

    int64_t n_st = nfa.st_kind.len;
    int64_t *vis = (int64_t *)calloc((size_t)n_st, sizeof(int64_t));
    int64_t *cur = (int64_t *)calloc((size_t)n_st, sizeof(int64_t));
    int64_t *nxt = (int64_t *)calloc((size_t)n_st, sizeof(int64_t));
    int64_t *stk = (int64_t *)calloc((size_t)(n_st * 2), sizeof(int64_t));
    int64_t gen_box = 0;
    int64_t line[256];

    int64_t rng = 2463534242LL;
    int64_t matches = 0;
    int64_t weighted = 0;
    for (int64_t li = 0; li < 6000; li++) {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        int64_t n_tok = 8 + (rng % 10);
        int64_t tlen = 0;
        for (int64_t ti = 0; ti < n_tok; ti++) {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            int64_t idx = rng % 30;
            const char *tok = tokens[idx];
            int64_t tl = tok_lens[idx];
            for (int64_t ci = 0; ci < tl; ci++) {
                line[tlen++] = (int64_t)(unsigned char)tok[ci];
            }
        }
        for (int64_t pi = 0; pi < 6; pi++) {
            if (nfa_search(&nfa, nfa.start_st[pi], nfa.match_st[pi], line, tlen, vis, &gen_box, cur, nxt, stk)) {
                matches += 1;
                weighted = (weighted + (li + 1) * (pi + 1)) % 1000000007;
            }
        }
    }

    free(vis);
    free(cur);
    free(nxt);
    free(stk);
    iv_free(&nfa.st_kind);
    iv_free(&nfa.st_out1);
    iv_free(&nfa.st_out2);
    iv_free(&nfa.p_st);
    iv_free(&nfa.p_wh);
    iv_free(&nfa.p_next);
    printf("%" PRId64 "\n%" PRId64 "\n", matches, weighted);
    return 0;
}
