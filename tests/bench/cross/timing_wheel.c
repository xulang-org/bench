#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MOD_V 1000000007LL
#define MAX_NODES 131072

typedef struct {
    int64_t *t_exp;
    int64_t *t_per;
    int *t_rep;
    int64_t *t_pay;
    int *t_st;
    int *t_prev;
    int *t_next;
    int *t_bkt;
    int b_head[512];
    int b_tail[512];
    int *free_stack;
    int free_top;
} Wheel;

static void init_wheel(Wheel *w) {
    w->t_exp = (int64_t *)calloc(MAX_NODES, sizeof(int64_t));
    w->t_per = (int64_t *)calloc(MAX_NODES, sizeof(int64_t));
    w->t_rep = (int *)calloc(MAX_NODES, sizeof(int));
    w->t_pay = (int64_t *)calloc(MAX_NODES, sizeof(int64_t));
    w->t_st = (int *)calloc(MAX_NODES, sizeof(int));
    w->t_prev = (int *)malloc(MAX_NODES * sizeof(int));
    w->t_next = (int *)malloc(MAX_NODES * sizeof(int));
    w->t_bkt = (int *)malloc(MAX_NODES * sizeof(int));
    w->free_stack = (int *)malloc(MAX_NODES * sizeof(int));
    w->free_top = MAX_NODES;
    for (int i = 0; i < MAX_NODES; i++) {
        w->t_prev[i] = -1;
        w->t_next[i] = -1;
        w->t_bkt[i] = -1;
        w->free_stack[i] = MAX_NODES - 1 - i;
    }
    for (int i = 0; i < 512; i++) {
        w->b_head[i] = -1;
        w->b_tail[i] = -1;
    }
}

static void free_wheel(Wheel *w) {
    free(w->t_exp);
    free(w->t_per);
    free(w->t_rep);
    free(w->t_pay);
    free(w->t_st);
    free(w->t_prev);
    free(w->t_next);
    free(w->t_bkt);
    free(w->free_stack);
}

static void bkt_push(Wheel *w, int b, int u) {
    int tail = w->b_tail[b];
    w->t_prev[u] = tail;
    w->t_next[u] = -1;
    w->t_bkt[u] = b;
    if (tail != -1) {
        w->t_next[tail] = u;
    } else {
        w->b_head[b] = u;
    }
    w->b_tail[b] = u;
}

static void bkt_remove(Wheel *w, int u) {
    int b = w->t_bkt[u];
    int pr = w->t_prev[u];
    int nx = w->t_next[u];
    if (pr != -1) {
        w->t_next[pr] = nx;
    } else {
        w->b_head[b] = nx;
    }
    if (nx != -1) {
        w->t_prev[nx] = pr;
    } else {
        w->b_tail[b] = pr;
    }
    w->t_prev[u] = -1;
    w->t_next[u] = -1;
    w->t_bkt[u] = -1;
}

static void schedule_node(Wheel *w, int u, int64_t exp, int64_t now) {
    w->t_exp[u] = exp;
    w->t_st[u] = 1;
    if ((exp - now) < 256) {
        bkt_push(w, (int)(exp & 255LL), u);
    } else {
        bkt_push(w, 256 + (int)((exp >> 8) & 255LL), u);
    }
}

int main(void) {
    const int ring_h = 16384;
    Wheel w;
    init_wheel(&w);
    int64_t rng = 888777666LL;

    int handles[16384];
    for (int i = 0; i < ring_h; i++) {
        handles[i] = -1;
    }

    int h_wr = 0;
    int64_t fired = 0;
    int64_t canceled = 0;
    int64_t ck = 0;

    for (int64_t now = 0; now < 160000; now++) {
        for (int k = 0; k < 3; k++) {
            if (w.free_top > 0) {
                w.free_top--;
                int u = w.free_stack[w.free_top];
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int64_t delay;
                if ((rng % 10LL) < 6LL) {
                    rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                    delay = 1LL + (rng % 250LL);
                } else {
                    rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                    delay = 256LL + (rng % 4096LL);
                }
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int64_t per = 0;
                int rep = 0;
                if ((rng % 5LL) == 0) {
                    rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                    per = 17LL + (rng % 200LL);
                    rep = 2;
                }
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int64_t pay = rng % 100000LL;
                w.t_per[u] = per;
                w.t_rep[u] = rep;
                w.t_pay[u] = pay;
                schedule_node(&w, u, now + delay, now);
                handles[h_wr] = u;
                h_wr = (h_wr + 1) & 16383;
            }
        }

        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int ci = (int)(rng & 16383LL);
        int cu = handles[ci];
        if (cu != -1 && w.t_st[cu] == 1) {
            bkt_remove(&w, cu);
            w.t_st[cu] = 0;
            w.free_stack[w.free_top++] = cu;
            handles[ci] = -1;
            canceled++;
        }

        int64_t tick = now + 1;
        if ((tick & 255LL) == 0) {
            int cb = 256 + (int)((tick >> 8) & 255LL);
            int u = w.b_head[cb];
            w.b_head[cb] = -1;
            w.b_tail[cb] = -1;
            while (u != -1) {
                int nx = w.t_next[u];
                w.t_prev[u] = -1;
                w.t_next[u] = -1;
                w.t_bkt[u] = -1;
                bkt_push(&w, (int)(w.t_exp[u] & 255LL), u);
                u = nx;
            }
        }

        int b0 = (int)(tick & 255LL);
        int u = w.b_head[b0];
        w.b_head[b0] = -1;
        w.b_tail[b0] = -1;
        while (u != -1) {
            int nx = w.t_next[u];
            w.t_prev[u] = -1;
            w.t_next[u] = -1;
            w.t_bkt[u] = -1;
            fired++;
            ck = (ck * 31LL + w.t_pay[u] * 7LL + tick) % MOD_V;
            if (w.t_rep[u] > 0) {
                w.t_rep[u]--;
                schedule_node(&w, u, tick + w.t_per[u], tick);
            } else {
                w.t_st[u] = 0;
                w.free_stack[w.free_top++] = u;
            }
            u = nx;
        }
    }

    ck = (ck * 37LL + canceled) % MOD_V;
    printf("%" PRId64 "\n%" PRId64 "\n", fired, ck);
    free_wheel(&w);
    return 0;
}
