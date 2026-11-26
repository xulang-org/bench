#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>

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

static void push_str(IntVec *buf, const char *s) {
    for (int64_t i = 0; s[i] != '\0'; i++) {
        iv_push(buf, (int64_t)(unsigned char)s[i]);
    }
}

static void push_int(IntVec *buf, int64_t x) {
    if (x < 0) {
        iv_push(buf, 45);
        x = -x;
    }
    if (x == 0) {
        iv_push(buf, 48);
        return;
    }
    int64_t digs[32];
    int64_t dc = 0;
    while (x > 0) {
        digs[dc++] = 48 + (x % 10);
        x /= 10;
    }
    for (int64_t i = dc - 1; i >= 0; i--) {
        iv_push(buf, digs[i]);
    }
}

static IntVec build_json_payload(void) {
    IntVec buf;
    iv_init(&buf, 8192);
    push_str(&buf, "{\"meta\":{\"id\":1000,\"active\":true,\"deleted\":false,\"note\":null,\"ratio\":-12.375e2},\"records\":[");
    for (int64_t r = 0; r < 48; r++) {
        if (r > 0) {
            iv_push(&buf, 44);
        }
        int64_t v0 = (r * 37 + 11) % 997 - 400;
        int64_t v1 = (r * 53 + 7) % 503;
        int64_t v2 = -(r * 19 + 3);
        int64_t v3 = r * 7 + 1;
        push_str(&buf, "{\"id\":");
        push_int(&buf, r);
        push_str(&buf, ",\"name\":\"item_");
        push_int(&buf, r);
        iv_push(&buf, 92);
        iv_push(&buf, 34);
        iv_push(&buf, 118);
        iv_push(&buf, 92);
        iv_push(&buf, 92);
        iv_push(&buf, 110);
        iv_push(&buf, 34);
        if (r % 2 == 0) {
            push_str(&buf, ",\"ok\":true,\"err\":null,\"vals\":[");
        } else {
            push_str(&buf, ",\"ok\":false,\"err\":null,\"vals\":[");
        }
        push_int(&buf, v0);
        iv_push(&buf, 44);
        push_int(&buf, v1);
        iv_push(&buf, 46);
        iv_push(&buf, 48 + (r % 10));
        iv_push(&buf, 44);
        push_int(&buf, v2);
        push_str(&buf, "e1,");
        push_int(&buf, v3);
        push_str(&buf, "],\"cfg\":{\"a\":");
        push_int(&buf, r * 3 + 1);
        push_str(&buf, ",\"b\":\"tag_");
        iv_push(&buf, 48 + (r % 7));
        push_str(&buf, "\",\"c\":[true,false,null]}}");
    }
    push_str(&buf, "]}");
    return buf;
}

typedef struct {
    const int64_t *buf;
    int64_t pos;
    int64_t n;
    IntVec kind;
    IntVec val;
    IntVec first_child;
    IntVec next_sib;
} JsonParser;

static int64_t new_node(JsonParser *p, int64_t k, int64_t v) {
    int64_t idx = p->kind.len;
    iv_push(&p->kind, k);
    iv_push(&p->val, v);
    iv_push(&p->first_child, -1);
    iv_push(&p->next_sib, -1);
    return idx;
}

static void skip_ws(JsonParser *p) {
    while (p->pos < p->n) {
        int64_t c = p->buf[p->pos];
        if (c == 32 || c == 9 || c == 10 || c == 13) {
            p->pos += 1;
        } else {
            break;
        }
    }
}

static int64_t parse_string_hash(JsonParser *p) {
    p->pos += 1;
    int64_t h = 0;
    while (p->pos < p->n) {
        int64_t c = p->buf[p->pos++];
        if (c == 34) {
            return h;
        }
        if (c == 92) {
            if (p->pos < p->n) {
                int64_t ec = p->buf[p->pos++];
                h = (h * 131 + ec + 256) % 1000000007;
            }
        } else {
            h = (h * 131 + c) % 1000000007;
        }
    }
    return h;
}

static int64_t parse_number_hash(JsonParser *p) {
    int64_t h = 0;
    if (p->pos < p->n && p->buf[p->pos] == 45) {
        h = 45;
        p->pos += 1;
    }
    while (p->pos < p->n && p->buf[p->pos] >= 48 && p->buf[p->pos] <= 57) {
        h = (h * 131 + p->buf[p->pos++]) % 1000000007;
    }
    if (p->pos < p->n && p->buf[p->pos] == 46) {
        h = (h * 131 + 46) % 1000000007;
        p->pos += 1;
        while (p->pos < p->n && p->buf[p->pos] >= 48 && p->buf[p->pos] <= 57) {
            h = (h * 131 + p->buf[p->pos++]) % 1000000007;
        }
    }
    if (p->pos < p->n && (p->buf[p->pos] == 101 || p->buf[p->pos] == 69)) {
        h = (h * 131 + 101) % 1000000007;
        p->pos += 1;
        if (p->pos < p->n && (p->buf[p->pos] == 43 || p->buf[p->pos] == 45)) {
            h = (h * 131 + p->buf[p->pos++]) % 1000000007;
        }
        while (p->pos < p->n && p->buf[p->pos] >= 48 && p->buf[p->pos] <= 57) {
            h = (h * 131 + p->buf[p->pos++]) % 1000000007;
        }
    }
    return h;
}

static int64_t parse_val(JsonParser *p) {
    skip_ws(p);
    int64_t c = p->buf[p->pos];
    if (c == 123) {
        p->pos += 1;
        int64_t node = new_node(p, 6, 0);
        skip_ws(p);
        if (p->pos < p->n && p->buf[p->pos] == 125) {
            p->pos += 1;
            return node;
        }
        int64_t tail = -1;
        int64_t cnt = 0;
        while (p->pos < p->n) {
            skip_ws(p);
            int64_t kh = parse_string_hash(p);
            skip_ws(p);
            p->pos += 1;
            int64_t child = parse_val(p);
            p->val.data[node] = (p->val.data[node] * 31 + kh) % 1000000007;
            if (tail == -1) {
                p->first_child.data[node] = child;
            } else {
                p->next_sib.data[tail] = child;
            }
            tail = child;
            cnt += 1;
            skip_ws(p);
            if (p->pos < p->n && p->buf[p->pos] == 44) {
                p->pos += 1;
            } else {
                p->pos += 1;
                break;
            }
        }
        p->val.data[node] = (p->val.data[node] * 31 + cnt) % 1000000007;
        return node;
    } else if (c == 91) {
        p->pos += 1;
        int64_t node = new_node(p, 5, 0);
        skip_ws(p);
        if (p->pos < p->n && p->buf[p->pos] == 93) {
            p->pos += 1;
            return node;
        }
        int64_t tail = -1;
        int64_t cnt = 0;
        while (p->pos < p->n) {
            int64_t child = parse_val(p);
            if (tail == -1) {
                p->first_child.data[node] = child;
            } else {
                p->next_sib.data[tail] = child;
            }
            tail = child;
            cnt += 1;
            skip_ws(p);
            if (p->pos < p->n && p->buf[p->pos] == 44) {
                p->pos += 1;
            } else {
                p->pos += 1;
                break;
            }
        }
        p->val.data[node] = cnt;
        return node;
    } else if (c == 34) {
        return new_node(p, 4, parse_string_hash(p));
    } else if (c == 116) {
        p->pos += 4;
        return new_node(p, 2, 1);
    } else if (c == 102) {
        p->pos += 5;
        return new_node(p, 2, 0);
    } else if (c == 110) {
        p->pos += 4;
        return new_node(p, 1, 0);
    } else {
        return new_node(p, 3, parse_number_hash(p));
    }
}

static int64_t walk(const JsonParser *p, int64_t u) {
    int64_t h = (p->kind.data[u] * 1000003 + p->val.data[u]) % 1000000007;
    int64_t ch = p->first_child.data[u];
    while (ch != -1) {
        h = (h * 31 + walk(p, ch)) % 1000000007;
        ch = p->next_sib.data[ch];
    }
    return h;
}

int main(void) {
    IntVec buf = build_json_payload();
    int64_t tot_nodes = 0;
    int64_t tot_hash = 0;
    for (int64_t r = 0; r < 400; r++) {
        int64_t v = 1000 + r;
        buf.data[14] = 48 + (v / 1000) % 10;
        buf.data[15] = 48 + (v / 100) % 10;
        buf.data[16] = 48 + (v / 10) % 10;
        buf.data[17] = 48 + v % 10;
        JsonParser p;
        p.buf = buf.data;
        p.pos = 0;
        p.n = buf.len;
        iv_init(&p.kind, 1024);
        iv_init(&p.val, 1024);
        iv_init(&p.first_child, 1024);
        iv_init(&p.next_sib, 1024);
        int64_t root = parse_val(&p);
        tot_nodes += p.kind.len;
        tot_hash = (tot_hash + walk(&p, root)) % 1000000007;
        iv_free(&p.kind);
        iv_free(&p.val);
        iv_free(&p.first_child);
        iv_free(&p.next_sib);
    }
    iv_free(&buf);
    printf("%" PRId64 "\n%" PRId64 "\n", tot_nodes, tot_hash);
    return 0;
}
