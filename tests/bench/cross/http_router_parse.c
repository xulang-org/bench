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
    if (x < 0) {
        vec_push(v, 45);
        x = -x;
    }
    if (x == 0) {
        vec_push(v, 48);
        return;
    }
    int64_t digs[24];
    int dc = 0;
    while (x > 0) {
        digs[dc++] = 48 + (x % 10);
        x /= 10;
    }
    for (int i = dc - 1; i >= 0; i--) {
        vec_push(v, digs[i]);
    }
}

static int64_t hex_val(int64_t b) {
    if (b >= 48 && b <= 57) return b - 48;
    if (b >= 65 && b <= 70) return b - 55;
    if (b >= 97 && b <= 102) return b - 87;
    return -1;
}

static int64_t decode_pct_hash(const int64_t *buf, int start, int end) {
    int64_t h = 0;
    int i = start;
    while (i < end) {
        int64_t b = buf[i];
        int64_t ch = b;
        if (b == 43) {
            ch = 32;
            i++;
        } else if (b == 37 && i + 2 < end) {
            int64_t hi = hex_val(buf[i + 1]);
            int64_t lo = hex_val(buf[i + 2]);
            if (hi >= 0 && lo >= 0) {
                ch = (hi << 4) | lo;
                i += 3;
            } else {
                i++;
            }
        } else {
            i++;
        }
        h = (h * 131 + ch) % MOD_V;
    }
    return h;
}

typedef struct {
    int node_edge_head[64];
    int node_param[64];
    int node_wild[64];
    int node_routes[64 * 5];
    int node_cnt;
    int edge_off[64];
    int edge_len[64];
    int edge_child[64];
    int edge_next[64];
    int edge_cnt;
    int64_t seg_pool[512];
    int pool_len;
} TrieRouter;

static int new_node(TrieRouter *rt) {
    int idx = rt->node_cnt++;
    rt->node_edge_head[idx] = -1;
    rt->node_param[idx] = -1;
    rt->node_wild[idx] = -1;
    for (int m = 0; m < 5; m++) rt->node_routes[idx * 5 + m] = 0;
    return idx;
}

static int eq_slice_str(const int64_t *pool, int off, int ln, const char *s) {
    int slen = (int)strlen(s);
    if (ln != slen) return 0;
    for (int i = 0; i < ln; i++) {
        if (pool[off + i] != (int64_t)(unsigned char)s[i]) return 0;
    }
    return 1;
}

static int eq_buf_pool(const int64_t *buf, int s, int ln, const int64_t *pool, int off, int plen) {
    if (ln != plen) return 0;
    for (int i = 0; i < ln; i++) {
        if (buf[s + i] != pool[off + i]) return 0;
    }
    return 1;
}

static void add_route(TrieRouter *rt, int method, const char *const *pat, int pat_len, int rid) {
    int cur = 0;
    for (int i = 0; i < pat_len; i++) {
        const char *seg = pat[i];
        if (strcmp(seg, "*") == 0) {
            if (rt->node_wild[cur] < 0) rt->node_wild[cur] = new_node(rt);
            cur = rt->node_wild[cur];
        } else if (seg[0] == ':') {
            if (rt->node_param[cur] < 0) rt->node_param[cur] = new_node(rt);
            cur = rt->node_param[cur];
        } else {
            int e = rt->node_edge_head[cur];
            int found = -1;
            while (e >= 0) {
                if (eq_slice_str(rt->seg_pool, rt->edge_off[e], rt->edge_len[e], seg)) {
                    found = e;
                    break;
                }
                e = rt->edge_next[e];
            }
            if (found >= 0) {
                cur = rt->edge_child[found];
            } else {
                int nxt = new_node(rt);
                int off = rt->pool_len;
                int slen = (int)strlen(seg);
                for (int j = 0; j < slen; j++) rt->seg_pool[rt->pool_len++] = (int64_t)(unsigned char)seg[j];
                int ei = rt->edge_cnt++;
                rt->edge_off[ei] = off;
                rt->edge_len[ei] = slen;
                rt->edge_child[ei] = nxt;
                rt->edge_next[ei] = rt->node_edge_head[cur];
                rt->node_edge_head[cur] = ei;
                cur = nxt;
            }
        }
    }
    rt->node_routes[cur * 5 + method] = rid;
}

static int match_lower_key(const int64_t *buf, int s, int e, const char *target, int tlen) {
    if (e - s != tlen) return 0;
    for (int i = 0; i < tlen; i++) {
        int64_t c = buf[s + i];
        if (c >= 65 && c <= 90) c += 32;
        if (c != (int64_t)(unsigned char)target[i]) return 0;
    }
    return 1;
}

int main(void) {
    TrieRouter rt;
    rt.node_cnt = 0;
    rt.edge_cnt = 0;
    rt.pool_len = 0;
    new_node(&rt);

    const char *p1[] = {"health"};
    const char *p2[] = {"metrics"};
    const char *p3[] = {"api", "v1", "users", ":id"};
    const char *p4[] = {"api", "v1", "users"};
    const char *p5[] = {"api", "v1", "users", ":id", "posts", ":pid"};
    const char *p6[] = {"api", "v1", "users", ":id", "posts", ":pid"};
    const char *p7[] = {"api", "v1", "orders", ":oid", "items"};
    const char *p8[] = {"api", "v1", "orders", ":oid", "status"};
    const char *p9[] = {"api", "v1", "orgs", ":org", "repos", ":repo", "issues", ":num"};
    const char *p10[] = {"api", "v1", "orgs", ":org", "repos", ":repo", "issues"};
    const char *p11[] = {"api", "v2", "search"};
    const char *p12[] = {"static", "*"};
    add_route(&rt, 1, p1, 1, 1);
    add_route(&rt, 1, p2, 1, 2);
    add_route(&rt, 1, p3, 4, 3);
    add_route(&rt, 2, p4, 3, 4);
    add_route(&rt, 1, p5, 6, 5);
    add_route(&rt, 4, p6, 6, 6);
    add_route(&rt, 1, p7, 5, 7);
    add_route(&rt, 3, p8, 5, 8);
    add_route(&rt, 1, p9, 8, 9);
    add_route(&rt, 2, p10, 7, 10);
    add_route(&rt, 1, p11, 3, 11);
    add_route(&rt, 1, p12, 2, 12);

    const char *users[8] = {"alice", "bob42", "charlie", "dana_9", "eve", "frank01", "grace", "heidi"};
    const char *orgs[4] = {"xulang", "acme", "nebula", "kernel"};
    const char *repos[5] = {"xu", "bench", "runtime", "stdlib", "docs"};
    const char *queries[6] = {
        "page=2&limit=50&q=hello+world%21",
        "sort=desc&filter=open%2Factive&tag=v1%2E0",
        "q=%41%42%43+test%20case&offset=100",
        "",
        "lang=zh%2DCN&mode=fast&debug=1",
        "path=%2Fusr%2Fbin&retry=3",
    };

    Vec64 req_buf;
    vec_init(&req_buf, 65536);
    int req_off[240];
    int req_len[240];
    int64_t rng = 246813579;
    for (int i = 0; i < 240; i++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int64_t k = rng % 14;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        const char *u = users[rng % 8];
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int64_t pid = 100 + (rng % 900);
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int64_t oid = 10000 + (rng % 90000);
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        const char *org = orgs[rng % 4];
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        const char *repo = repos[rng % 5];
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int64_t num = 1 + (rng % 500);
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        const char *q = queries[rng % 6];
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int64_t cl = rng % 4096;

        int off = req_buf.len;
        req_off[i] = off;
        if (k == 0) push_str(&req_buf, "GET /health");
        else if (k == 1) push_str(&req_buf, "GET /metrics");
        else if (k == 2) { push_str(&req_buf, "GET /api/v1/users/"); push_str(&req_buf, u); }
        else if (k == 3) push_str(&req_buf, "POST /api/v1/users");
        else if (k == 4) { push_str(&req_buf, "GET /api/v1/users/"); push_str(&req_buf, u); push_str(&req_buf, "/posts/"); push_int(&req_buf, pid); }
        else if (k == 5) { push_str(&req_buf, "DELETE /api/v1/users/"); push_str(&req_buf, u); push_str(&req_buf, "/posts/"); push_int(&req_buf, pid); }
        else if (k == 6) { push_str(&req_buf, "GET /api/v1/orders/"); push_int(&req_buf, oid); push_str(&req_buf, "/items"); }
        else if (k == 7) { push_str(&req_buf, "PUT /api/v1/orders/"); push_int(&req_buf, oid); push_str(&req_buf, "/status"); }
        else if (k == 8) { push_str(&req_buf, "GET /api/v1/orgs/"); push_str(&req_buf, org); push_str(&req_buf, "/repos/"); push_str(&req_buf, repo); push_str(&req_buf, "/issues/"); push_int(&req_buf, num); }
        else if (k == 9) { push_str(&req_buf, "POST /api/v1/orgs/"); push_str(&req_buf, org); push_str(&req_buf, "/repos/"); push_str(&req_buf, repo); push_str(&req_buf, "/issues"); }
        else if (k == 10) push_str(&req_buf, "GET /api/v2/search");
        else if (k == 11) { push_str(&req_buf, "GET /static/js/"); push_str(&req_buf, repo); push_str(&req_buf, "/bundle_"); push_int(&req_buf, pid); push_str(&req_buf, ".js"); }
        else if (k == 12) { push_str(&req_buf, "GET /api/v1/unknown/"); push_str(&req_buf, u); push_str(&req_buf, "/nope"); }
        else push_str(&req_buf, "POST /health");

        if (q[0]) {
            vec_push(&req_buf, 63);
            push_str(&req_buf, q);
        }
        push_str(&req_buf, " HTTP/1.1\r\n");
        if ((i % 3) != 0) push_str(&req_buf, "Host: api.xulang.org\r\n");
        else push_str(&req_buf, "HOST: api.xulang.org\r\n");
        push_str(&req_buf, "User-Agent: xu-bench/1.0\r\n");
        if ((i & 1) == 0) push_str(&req_buf, "Content-Length: ");
        else push_str(&req_buf, "content-length: ");
        push_int(&req_buf, cl);
        push_str(&req_buf, "\r\nX-Request-Id: req-");
        push_int(&req_buf, i);
        vec_push(&req_buf, 45);
        push_int(&req_buf, num);
        push_str(&req_buf, "\r\n\r\n");
        req_len[i] = req_buf.len - off;
    }

    const int64_t *buf = req_buf.data;
    int seg_starts[16], seg_ends[16];
    int64_t matched = 0, ck = 0;
    for (int rnd = 0; rnd < 500; rnd++) {
        for (int ri = 0; ri < 240; ri++) {
            int r_start = req_off[ri];
            int r_end = r_start + req_len[ri];
            int sp1 = r_start;
            while (buf[sp1] != 32) sp1++;
            int mlen = sp1 - r_start;
            int64_t mc = 0;
            if (mlen == 3 && buf[r_start] == 71) mc = 1;
            else if (mlen == 4 && buf[r_start] == 80) mc = 2;
            else if (mlen == 3 && buf[r_start] == 80) mc = 3;
            else if (mlen == 6 && buf[r_start] == 68) mc = 4;

            int t_start = sp1 + 1;
            int sp2 = t_start;
            while (buf[sp2] != 32) sp2++;
            int crlf = sp2 + 1;
            while (!(buf[crlf] == 13 && buf[crlf + 1] == 10)) crlf++;
            int qpos = -1;
            for (int p = t_start; p < sp2; p++) {
                if (buf[p] == 63) { qpos = p; break; }
            }
            int path_end = qpos >= 0 ? qpos : sp2;
            int n_segs = 0, sp = t_start;
            while (sp < path_end) {
                while (sp < path_end && buf[sp] == 47) sp++;
                if (sp >= path_end) break;
                int se = sp;
                while (se < path_end && buf[se] != 47) se++;
                seg_starts[n_segs] = sp;
                seg_ends[n_segs] = se;
                n_segs++;
                sp = se;
            }

            int pos = crlf + 2;
            int64_t hdr_cnt = 0, content_len = 0, req_id_hash = 0;
            while (pos < r_end) {
                int lend = pos;
                while (lend + 1 < r_end && !(buf[lend] == 13 && buf[lend + 1] == 10)) lend++;
                if (lend == pos) break;
                int col = pos;
                while (col < lend && buf[col] != 58) col++;
                int vs = col + 1;
                while (vs < lend && (buf[vs] == 32 || buf[vs] == 9)) vs++;
                int ve = lend;
                while (ve > vs && (buf[ve - 1] == 32 || buf[ve - 1] == 9)) ve--;
                hdr_cnt++;
                if (match_lower_key(buf, pos, col, "content-length", 14)) {
                    int64_t v = 0;
                    for (int vp = vs; vp < ve; vp++) v = v * 10 + (buf[vp] - 48);
                    content_len = v;
                } else if (match_lower_key(buf, pos, col, "x-request-id", 12)) {
                    for (int vp = vs; vp < ve; vp++) req_id_hash = (req_id_hash * 31 + buf[vp]) % MOD_V;
                }
                pos = lend + 2;
            }

            int cur = 0, sj = 0, dead = 0;
            int64_t ph = 0;
            while (sj < n_segs) {
                int ss = seg_starts[sj];
                int sln = seg_ends[sj] - ss;
                int e = rt.node_edge_head[cur], nxt = -1;
                while (e >= 0) {
                    if (eq_buf_pool(buf, ss, sln, rt.seg_pool, rt.edge_off[e], rt.edge_len[e])) {
                        nxt = rt.edge_child[e];
                        break;
                    }
                    e = rt.edge_next[e];
                }
                if (nxt >= 0) {
                    cur = nxt;
                    sj++;
                } else if (rt.node_param[cur] >= 0) {
                    int ce = ss + sln;
                    for (int cp = ss; cp < ce; cp++) ph = (ph * 131 + buf[cp]) % MOD_V;
                    cur = rt.node_param[cur];
                    sj++;
                } else if (rt.node_wild[cur] >= 0) {
                    while (sj < n_segs) {
                        int ce = seg_ends[sj];
                        for (int cp = seg_starts[sj]; cp < ce; cp++) ph = (ph * 131 + buf[cp]) % MOD_V;
                        sj++;
                    }
                    cur = rt.node_wild[cur];
                    break;
                } else {
                    dead = 1;
                    break;
                }
            }
            int64_t route_id = 0, param_hash = 0;
            if (!dead) {
                int rid = rt.node_routes[cur * 5 + (int)mc];
                if (rid > 0) { route_id = rid; param_hash = ph; }
            }
            int64_t q_hash = 0;
            if (qpos >= 0 && qpos + 1 < sp2) {
                int qp = qpos + 1;
                while (qp < sp2) {
                    int qe = qp;
                    while (qe < sp2 && buf[qe] != 38) qe++;
                    int eq = -1;
                    for (int qt = qp; qt < qe; qt++) {
                        if (buf[qt] == 61) { eq = qt; break; }
                    }
                    if (eq >= 0) {
                        int64_t kh = decode_pct_hash(buf, qp, eq);
                        int64_t vh = decode_pct_hash(buf, eq + 1, qe);
                        q_hash = (q_hash * 257 + kh * 17 + vh) % MOD_V;
                    } else {
                        q_hash = (q_hash * 257 + decode_pct_hash(buf, qp, qe)) % MOD_V;
                    }
                    qp = qe + 1;
                }
            }
            if (route_id > 0) matched++;
            int64_t row = (route_id * 1000003LL + mc * 97 + param_hash * 7 + q_hash * 13 + content_len * 3 + hdr_cnt * 19 + req_id_hash) % MOD_V;
            ck = (ck * 31 + row) % MOD_V;
        }
    }
    free(req_buf.data);
    printf("%" PRId64 "\n%" PRId64 "\n", matched, ck);
    return 0;
}
