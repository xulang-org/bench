#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MOD_V 1000000007LL

static int64_t mix32(int64_t x) {
    const int64_t mask = 4294967295LL;
    const int64_t mul = 73244475LL;
    int64_t h = x & mask;
    h = h ^ (h >> 16);
    h = (h * mul) & mask;
    h = h ^ (h >> 16);
    h = (h * mul) & mask;
    h = h ^ (h >> 16);
    return h;
}

static void sift_max_ring(int64_t *rt, int64_t *rn, int start, int n) {
    int i = start;
    while (1) {
        int l = i * 2 + 1;
        if (l >= n) {
            break;
        }
        int best = l;
        int r = l + 1;
        if (r < n && rt[r] > rt[best]) {
            best = r;
        }
        if (rt[i] < rt[best]) {
            int64_t tt = rt[i]; rt[i] = rt[best]; rt[best] = tt;
            int64_t tn = rn[i]; rn[i] = rn[best]; rn[best] = tn;
            i = best;
        } else {
            break;
        }
    }
}

static void heapsort_ring(int64_t *rt, int64_t *rn, int n) {
    for (int start = n / 2 - 1; start >= 0; start--) {
        sift_max_ring(rt, rn, start, n);
    }
    for (int end = n - 1; end > 0; end--) {
        int64_t tt = rt[0]; rt[0] = rt[end]; rt[end] = tt;
        int64_t tn = rn[0]; rn[0] = rn[end]; rn[end] = tn;
        sift_max_ring(rt, rn, 0, end);
    }
}

static int build_ring(const int64_t *alive, int64_t *ring_tok, int64_t *ring_node) {
    const int max_nodes = 48;
    const int vnodes = 128;
    const int64_t gold_c = 2654435769LL;
    int sz = 0;
    for (int nid = 0; nid < max_nodes; nid++) {
        if (alive[nid] == 1) {
            for (int v = 0; v < vnodes; v++) {
                ring_tok[sz] = mix32((((int64_t)nid << 10) | (int64_t)v) ^ gold_c);
                ring_node[sz] = nid;
                sz++;
            }
        }
    }
    heapsort_ring(ring_tok, ring_node, sz);
    return sz;
}

static int64_t route_tok(const int64_t *ring_tok, const int64_t *ring_node, int64_t tok, int sz) {
    int lo = 0;
    int hi = sz;
    while (lo < hi) {
        int mid = (lo + hi) >> 1;
        if (ring_tok[mid] < tok) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    if (lo == sz) {
        lo = 0;
    }
    return ring_node[lo];
}

int main(void) {
    const int64_t mask32 = 4294967295LL;
    const int max_nodes = 48;
    const int vnodes = 128;
    const int n_keys = 150000;

    int64_t alive[48];
    int64_t node_load[48];
    for (int nid = 0; nid < max_nodes; nid++) {
        alive[nid] = (nid < 32) ? 1 : 0;
        node_load[nid] = 0;
    }

    int64_t *ring_tok = (int64_t *)malloc((size_t)(max_nodes * vnodes) * sizeof(int64_t));
    int64_t *ring_node = (int64_t *)malloc((size_t)(max_nodes * vnodes) * sizeof(int64_t));
    int64_t *key_tok = (int64_t *)malloc((size_t)n_keys * sizeof(int64_t));
    int64_t *prev_owner = (int64_t *)malloc((size_t)n_keys * sizeof(int64_t));

    for (int i = 0; i < n_keys; i++) {
        key_tok[i] = mix32(((int64_t)i * 2654435761LL + 12345LL) & mask32);
    }

    int ring_sz = build_ring(alive, ring_tok, ring_node);
    int64_t ck = 0;
    for (int p = 0; p < 4; p++) {
        int64_t salt = (int64_t)p * 7919LL;
        for (int i = 0; i < n_keys; i++) {
            int64_t t = mix32((key_tok[i] + salt) & mask32);
            int64_t owner = route_tok(ring_tok, ring_node, t, ring_sz);
            node_load[owner]++;
            ck = (ck * 31LL + owner + 1LL) % MOD_V;
        }
    }

    for (int i = 0; i < n_keys; i++) {
        prev_owner[i] = route_tok(ring_tok, ring_node, key_tok[i], ring_sz);
    }

    int64_t total_moved = 0;
    for (int step = 0; step < 4; step++) {
        if (step == 0) {
            alive[32] = 1; alive[33] = 1; alive[34] = 1; alive[35] = 1;
        } else if (step == 1) {
            alive[5] = 0; alive[19] = 0;
        } else if (step == 2) {
            alive[36] = 1; alive[37] = 1; alive[38] = 1; alive[39] = 1; alive[40] = 1; alive[41] = 1;
        } else {
            alive[2] = 0; alive[11] = 0; alive[24] = 0; alive[33] = 0;
        }
        ring_sz = build_ring(alive, ring_tok, ring_node);
        int64_t moved = 0;
        for (int i = 0; i < n_keys; i++) {
            int64_t o = route_tok(ring_tok, ring_node, key_tok[i], ring_sz);
            if (o != prev_owner[i]) {
                moved++;
                prev_owner[i] = o;
            }
            ck = (ck * 31LL + o + 1LL) % MOD_V;
        }
        total_moved += moved;
        ck = (ck * 37LL + moved) % MOD_V;
    }

    for (int nid = 0; nid < max_nodes; nid++) {
        ck = (ck * 31LL + node_load[nid]) % MOD_V;
    }

    printf("%" PRId64 "\n%" PRId64 "\n", total_moved, ck);
    free(ring_tok);
    free(ring_node);
    free(key_tok);
    free(prev_owner);
    return 0;
}
