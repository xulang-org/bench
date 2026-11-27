#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MOD_V 1000000007LL

typedef struct {
    int64_t *mem;
    int page_cls[256];
    int page_used[256];
    int page_head[256];
    int page_prev[256];
    int page_next[256];
    int page_in_list[256];
    int cls_head[6];
    int free_stack[256];
    int free_top;
    int class_sz[6];
    int64_t page_allocs;
    int64_t page_reclaims;
} SlabArena;

static void init_slab(SlabArena *s) {
    s->mem = (int64_t *)calloc(256U * 256U, sizeof(int64_t));
    s->free_top = 256;
    s->page_allocs = 0;
    s->page_reclaims = 0;
    s->class_sz[0] = 2;
    s->class_sz[1] = 4;
    s->class_sz[2] = 8;
    s->class_sz[3] = 16;
    s->class_sz[4] = 32;
    s->class_sz[5] = 64;
    for (int i = 0; i < 256; i++) {
        s->page_cls[i] = -1;
        s->page_used[i] = 0;
        s->page_head[i] = -1;
        s->page_prev[i] = -1;
        s->page_next[i] = -1;
        s->page_in_list[i] = 0;
        s->free_stack[i] = 255 - i;
    }
    for (int i = 0; i < 6; i++) {
        s->cls_head[i] = -1;
    }
}

static void list_push(SlabArena *s, int cls, int pg) {
    int h = s->cls_head[cls];
    s->page_prev[pg] = -1;
    s->page_next[pg] = h;
    if (h != -1) {
        s->page_prev[h] = pg;
    }
    s->cls_head[cls] = pg;
    s->page_in_list[pg] = 1;
}

static void list_remove(SlabArena *s, int cls, int pg) {
    int pr = s->page_prev[pg];
    int nx = s->page_next[pg];
    if (pr != -1) {
        s->page_next[pr] = nx;
    } else {
        s->cls_head[cls] = nx;
    }
    if (nx != -1) {
        s->page_prev[nx] = pr;
    }
    s->page_prev[pg] = -1;
    s->page_next[pg] = -1;
    s->page_in_list[pg] = 0;
}

static int slab_alloc(SlabArena *s, int cls) {
    int pg = s->cls_head[cls];
    if (pg == -1) {
        if (s->free_top == 0) {
            return -1;
        }
        s->free_top--;
        pg = s->free_stack[s->free_top];
        s->page_allocs++;
        s->page_cls[pg] = cls;
        s->page_used[pg] = 0;
        int sz = s->class_sz[cls];
        int base = pg << 8;
        int cnt = 256 / sz;
        for (int j = 0; j < cnt - 1; j++) {
            s->mem[base + j * sz] = base + (j + 1) * sz;
        }
        s->mem[base + (cnt - 1) * sz] = -1;
        s->page_head[pg] = base;
        list_push(s, cls, pg);
    }
    int ptr = s->page_head[pg];
    int nxt_ptr = (int)s->mem[ptr];
    s->page_head[pg] = nxt_ptr;
    s->page_used[pg]++;
    if (nxt_ptr == -1) {
        list_remove(s, cls, pg);
    }
    return ptr;
}

static void slab_free(SlabArena *s, int ptr) {
    int pg = ptr >> 8;
    int cls = s->page_cls[pg];
    int was_full = (s->page_head[pg] == -1) ? 1 : 0;
    s->mem[ptr] = s->page_head[pg];
    s->page_head[pg] = ptr;
    s->page_used[pg]--;
    if (s->page_used[pg] == 0) {
        if (s->page_in_list[pg] == 1) {
            list_remove(s, cls, pg);
        }
        s->page_cls[pg] = -1;
        s->page_head[pg] = -1;
        s->free_stack[s->free_top++] = pg;
        s->page_reclaims++;
    } else if (was_full == 1) {
        list_push(s, cls, pg);
    }
}

int main(void) {
    const int live = 1024;
    SlabArena s;
    init_slab(&s);
    int64_t rng = 31415926LL;

    int live_ptr[1024];
    int live_cls[1024];
    for (int i = 0; i < live; i++) {
        live_ptr[i] = -1;
        live_cls[i] = 0;
    }

    int64_t alloc_ok = 0;
    int64_t ck = 0;
    for (int64_t op_i = 0; op_i < 600000; op_i++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int slot = (int)(rng & 1023LL);
        if ((op_i & 4095LL) == 4095LL) {
            for (int k = 0; k < live; k += 3) {
                int p = live_ptr[k];
                if (p != -1) {
                    int sz = s.class_sz[live_cls[k]];
                    ck = (ck * 31LL + s.mem[p] + s.mem[p + sz - 1]) % MOD_V;
                    slab_free(&s, p);
                    live_ptr[k] = -1;
                }
            }
        }
        if (live_ptr[slot] != -1) {
            int p = live_ptr[slot];
            int sz = s.class_sz[live_cls[slot]];
            ck = (ck * 31LL + s.mem[p] + s.mem[p + sz - 1]) % MOD_V;
            slab_free(&s, p);
            live_ptr[slot] = -1;
        } else {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t r = rng % 100LL;
            int cls = 5;
            if (r < 35) cls = 0;
            else if (r < 60) cls = 1;
            else if (r < 78) cls = 2;
            else if (r < 90) cls = 3;
            else if (r < 97) cls = 4;
            int p = slab_alloc(&s, cls);
            if (p >= 0) {
                int sz = s.class_sz[cls];
                int64_t tag = (op_i * 13LL + (int64_t)cls * 7LL + 1LL) % MOD_V;
                s.mem[p] = tag;
                s.mem[p + sz - 1] = (tag ^ ((int64_t)p * 3LL)) % MOD_V;
                live_ptr[slot] = p;
                live_cls[slot] = cls;
                alloc_ok++;
            }
        }
    }

    for (int k = 0; k < live; k++) {
        int p = live_ptr[k];
        if (p != -1) {
            int sz = s.class_sz[live_cls[k]];
            ck = (ck * 31LL + s.mem[p] + s.mem[p + sz - 1]) % MOD_V;
            slab_free(&s, p);
            live_ptr[k] = -1;
        }
    }
    ck = (ck * 37LL + s.page_allocs * 17LL + s.page_reclaims) % MOD_V;
    printf("%" PRId64 "\n%" PRId64 "\n", alloc_ok, ck);
    free(s.mem);
    return 0;
}
