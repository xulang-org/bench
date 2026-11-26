#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int64_t *f;
    int64_t *n;
    int64_t len;
} Heap;

static void heap_push(Heap *h, int64_t fval, int64_t node) {
    int64_t i = h->len++;
    h->f[i] = fval;
    h->n[i] = node;
    while (i > 0) {
        int64_t p = (i - 1) / 2;
        if (h->f[p] > h->f[i] || (h->f[p] == h->f[i] && h->n[p] > h->n[i])) {
            int64_t tf = h->f[p]; h->f[p] = h->f[i]; h->f[i] = tf;
            int64_t tn = h->n[p]; h->n[p] = h->n[i]; h->n[i] = tn;
            i = p;
        } else {
            break;
        }
    }
}

static int64_t heap_pop(Heap *h) {
    int64_t top = h->n[0];
    int64_t sz = --h->len;
    if (sz > 0) {
        h->f[0] = h->f[sz];
        h->n[0] = h->n[sz];
        int64_t i = 0;
        while (1) {
            int64_t l = 2 * i + 1;
            if (l >= sz) break;
            int64_t r = l + 1;
            int64_t best = l;
            if (r < sz && (h->f[r] < h->f[l] || (h->f[r] == h->f[l] && h->n[r] < h->n[l]))) {
                best = r;
            }
            if (h->f[best] < h->f[i] || (h->f[best] == h->f[i] && h->n[best] < h->n[i])) {
                int64_t tf = h->f[i]; h->f[i] = h->f[best]; h->f[best] = tf;
                int64_t tn = h->n[i]; h->n[i] = h->n[best]; h->n[best] = tn;
                i = best;
            } else {
                break;
            }
        }
    }
    return top;
}

int main(void) {
    const int64_t W = 81;
    const int64_t H = 81;
    const int64_t N = 6561;
    const int64_t INF = 1000000000;
    const int64_t start = 82;
    const int64_t goal = 79 * 81 + 79;
    const int64_t gx = 79;
    const int64_t gy = 79;

    int64_t *grid = (int64_t *)malloc((size_t)N * sizeof(int64_t));
    int64_t *g_score = (int64_t *)malloc((size_t)N * sizeof(int64_t));
    int64_t *closed = (int64_t *)malloc((size_t)N * sizeof(int64_t));
    int64_t *stk_x = (int64_t *)malloc((size_t)N * sizeof(int64_t));
    int64_t *stk_y = (int64_t *)malloc((size_t)N * sizeof(int64_t));
    int64_t *hf = (int64_t *)malloc(32768 * sizeof(int64_t));
    int64_t *hn = (int64_t *)malloc(32768 * sizeof(int64_t));
    Heap h = {hf, hn, 0};

    const int64_t dx[4] = {0, 0, -2, 2};
    const int64_t dy[4] = {-2, 2, 0, 0};
    int64_t dirs[4];

    int64_t sum_d = 0;
    int64_t poly_d = 0;
    for (int64_t m = 0; m < 60; m++) {
        int64_t rng = 100003 + m * 9973;
        for (int64_t i = 0; i < N; i++) {
            grid[i] = 1;
            g_score[i] = INF;
            closed[i] = 0;
        }
        grid[start] = 0;
        int64_t sp = 1;
        stk_x[0] = 1;
        stk_y[0] = 1;
        while (sp > 0) {
            int64_t cx = stk_x[sp - 1];
            int64_t cy = stk_y[sp - 1];
            int64_t dc = 0;
            for (int64_t d = 0; d < 4; d++) {
                int64_t nx = cx + dx[d];
                int64_t ny = cy + dy[d];
                if (nx >= 1 && nx <= W - 2 && ny >= 1 && ny <= H - 2 && grid[ny * W + nx] == 1) {
                    dirs[dc++] = d;
                }
            }
            if (dc == 0) {
                sp -= 1;
            } else {
                rng = (rng * 1103515245 + 12345) & 2147483647;
                int64_t pick = dirs[rng % dc];
                int64_t nx = cx + dx[pick];
                int64_t ny = cy + dy[pick];
                int64_t mx = (cx + nx) / 2;
                int64_t my = (cy + ny) / 2;
                grid[my * W + mx] = 0;
                grid[ny * W + nx] = 0;
                stk_x[sp] = nx;
                stk_y[sp] = ny;
                sp += 1;
            }
        }

        for (int64_t y = 1; y < H - 1; y++) {
            for (int64_t x = 1; x < W - 1; x++) {
                int64_t idx = y * W + x;
                if (grid[idx] == 1) {
                    if ((grid[idx - 1] == 0 && grid[idx + 1] == 0) || (grid[idx - W] == 0 && grid[idx + W] == 0)) {
                        rng = (rng * 1103515245 + 12345) & 2147483647;
                        if ((rng % 100) < 12) {
                            grid[idx] = 0;
                        }
                    }
                }
            }
        }

        g_score[start] = 0;
        h.len = 0;
        heap_push(&h, 156, start);
        int64_t ans = -1;
        while (h.len > 0) {
            int64_t u = heap_pop(&h);
            if (closed[u] != 0) continue;
            closed[u] = 1;
            if (u == goal) {
                ans = g_score[u];
                break;
            }
            int64_t gu = g_score[u] + 1;
            int64_t ux = u % W;
            int64_t uy = u / W;

            if (uy > 0) {
                int64_t v = u - W;
                if (grid[v] == 0 && closed[v] == 0 && gu < g_score[v]) {
                    g_score[v] = gu;
                    int64_t dhx = gx - ux; if (dhx < 0) dhx = -dhx;
                    int64_t dhy = gy - (uy - 1); if (dhy < 0) dhy = -dhy;
                    heap_push(&h, gu + dhx + dhy, v);
                }
            }
            if (uy + 1 < H) {
                int64_t v = u + W;
                if (grid[v] == 0 && closed[v] == 0 && gu < g_score[v]) {
                    g_score[v] = gu;
                    int64_t dhx = gx - ux; if (dhx < 0) dhx = -dhx;
                    int64_t dhy = gy - (uy + 1); if (dhy < 0) dhy = -dhy;
                    heap_push(&h, gu + dhx + dhy, v);
                }
            }
            if (ux > 0) {
                int64_t v = u - 1;
                if (grid[v] == 0 && closed[v] == 0 && gu < g_score[v]) {
                    g_score[v] = gu;
                    int64_t dhx = gx - (ux - 1); if (dhx < 0) dhx = -dhx;
                    int64_t dhy = gy - uy; if (dhy < 0) dhy = -dhy;
                    heap_push(&h, gu + dhx + dhy, v);
                }
            }
            if (ux + 1 < W) {
                int64_t v = u + 1;
                if (grid[v] == 0 && closed[v] == 0 && gu < g_score[v]) {
                    g_score[v] = gu;
                    int64_t dhx = gx - (ux + 1); if (dhx < 0) dhx = -dhx;
                    int64_t dhy = gy - uy; if (dhy < 0) dhy = -dhy;
                    heap_push(&h, gu + dhx + dhy, v);
                }
            }
        }
        sum_d += ans;
        poly_d = (poly_d * 1000003 + ans) % 1000000007;
    }

    free(grid);
    free(g_score);
    free(closed);
    free(stk_x);
    free(stk_y);
    free(hf);
    free(hn);
    printf("%" PRId64 "\n%" PRId64 "\n", sum_d, poly_d);
    return 0;
}
