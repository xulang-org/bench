#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MOD_V 1000000007LL

static int less_rec(int64_t k1, int64_t s1, int64_t k2, int64_t s2) {
    if (k1 != k2) {
        return k1 < k2;
    }
    return s1 > s2;
}

static void swap_run(int64_t *rk, int64_t *rs, int64_t *rv, int64_t *rt, int a, int b) {
    int64_t tk = rk[a]; rk[a] = rk[b]; rk[b] = tk;
    int64_t ts = rs[a]; rs[a] = rs[b]; rs[b] = ts;
    int64_t tv = rv[a]; rv[a] = rv[b]; rv[b] = tv;
    int64_t tt = rt[a]; rt[a] = rt[b]; rt[b] = tt;
}

static void sift_max_run(int64_t *rk, int64_t *rs, int64_t *rv, int64_t *rt, int start, int n) {
    int i = start;
    while (1) {
        int l = i * 2 + 1;
        if (l >= n) {
            break;
        }
        int best = l;
        int r = l + 1;
        if (r < n && less_rec(rk[best], rs[best], rk[r], rs[r])) {
            best = r;
        }
        if (less_rec(rk[i], rs[i], rk[best], rs[best])) {
            swap_run(rk, rs, rv, rt, i, best);
            i = best;
        } else {
            break;
        }
    }
}

static void heapsort_run(int64_t *rk, int64_t *rs, int64_t *rv, int64_t *rt, int n) {
    for (int start = n / 2 - 1; start >= 0; start--) {
        sift_max_run(rk, rs, rv, rt, start, n);
    }
    for (int end = n - 1; end > 0; end--) {
        swap_run(rk, rs, rv, rt, 0, end);
        sift_max_run(rk, rs, rv, rt, 0, end);
    }
}

static int heap_less(const int64_t *all_k, const int64_t *all_s, const int *run_pos, int ra, int rb) {
    int pa = run_pos[ra];
    int pb = run_pos[rb];
    return less_rec(all_k[pa], all_s[pa], all_k[pb], all_s[pb]);
}

static void sift_min_merge(int *heap, int hsz, const int64_t *all_k, const int64_t *all_s, const int *run_pos) {
    int i = 0;
    while (1) {
        int l = i * 2 + 1;
        if (l >= hsz) {
            break;
        }
        int best = l;
        int rr = l + 1;
        if (rr < hsz && heap_less(all_k, all_s, run_pos, heap[rr], heap[best])) {
            best = rr;
        }
        if (heap_less(all_k, all_s, run_pos, heap[best], heap[i])) {
            int tmp = heap[i];
            heap[i] = heap[best];
            heap[best] = tmp;
            i = best;
        } else {
            break;
        }
    }
}

int main(void) {
    int64_t rng = 555123456LL;
    int64_t global_seq = 1;
    int64_t *l1_k = NULL;
    int64_t *l1_v = NULL;
    int n_l1 = 0;
    int64_t hits = 0;
    int64_t ck = 0;

    int64_t *rk = (int64_t *)malloc(12000U * sizeof(int64_t));
    int64_t *rs = (int64_t *)malloc(12000U * sizeof(int64_t));
    int64_t *rv = (int64_t *)malloc(12000U * sizeof(int64_t));
    int64_t *rt = (int64_t *)malloc(12000U * sizeof(int64_t));

    int max_all = 140000;
    int64_t *all_k = (int64_t *)malloc((size_t)max_all * sizeof(int64_t));
    int64_t *all_s = (int64_t *)malloc((size_t)max_all * sizeof(int64_t));
    int64_t *all_v = (int64_t *)malloc((size_t)max_all * sizeof(int64_t));
    int64_t *all_t = (int64_t *)malloc((size_t)max_all * sizeof(int64_t));

    for (int cyc = 0; cyc < 4; cyc++) {
        int all_len = 0;
        int run_pos[9];
        int run_end[9];
        int nruns = 0;

        for (int rn = 0; rn < 8; rn++) {
            for (int j = 0; j < 12000; j++) {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int64_t k = rng % 40000LL;
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int64_t tomb = ((rng % 10LL) == 0) ? 1 : 0;
                int64_t val = 0;
                if (tomb == 0) {
                    rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                    val = 1 + (rng % 100000LL);
                }
                rk[j] = k;
                rs[j] = global_seq;
                rv[j] = val;
                rt[j] = tomb;
                global_seq++;
            }
            heapsort_run(rk, rs, rv, rt, 12000);
            int st = all_len;
            int64_t prev_k = -1;
            for (int j = 0; j < 12000; j++) {
                if (rk[j] != prev_k) {
                    all_k[all_len] = rk[j];
                    all_s[all_len] = rs[j];
                    all_v[all_len] = rv[j];
                    all_t[all_len] = rt[j];
                    all_len++;
                    prev_k = rk[j];
                }
            }
            run_pos[nruns] = st;
            run_end[nruns] = all_len;
            nruns++;
        }

        if (n_l1 > 0) {
            int st = all_len;
            for (int j = 0; j < n_l1; j++) {
                all_k[all_len] = l1_k[j];
                all_s[all_len] = 0;
                all_v[all_len] = l1_v[j];
                all_t[all_len] = 0;
                all_len++;
            }
            run_pos[nruns] = st;
            run_end[nruns] = all_len;
            nruns++;
        }

        int heap[9];
        int hsz = 0;
        for (int r = 0; r < nruns; r++) {
            if (run_pos[r] < run_end[r]) {
                heap[hsz] = r;
                int hi = hsz;
                hsz++;
                while (hi > 0) {
                    int p = (hi - 1) >> 1;
                    if (heap_less(all_k, all_s, run_pos, heap[hi], heap[p])) {
                        int tmp = heap[hi];
                        heap[hi] = heap[p];
                        heap[p] = tmp;
                        hi = p;
                    } else {
                        break;
                    }
                }
            }
        }

        int64_t *new_k = (int64_t *)malloc(40000U * sizeof(int64_t));
        int64_t *new_v = (int64_t *)malloc(40000U * sizeof(int64_t));
        int new_len = 0;
        int64_t last_k = -1;
        while (hsz > 0) {
            int top_r = heap[0];
            int pos = run_pos[top_r];
            int64_t k = all_k[pos];
            int64_t v = all_v[pos];
            int64_t t = all_t[pos];
            run_pos[top_r] = pos + 1;
            if (run_pos[top_r] < run_end[top_r]) {
                sift_min_merge(heap, hsz, all_k, all_s, run_pos);
            } else {
                hsz--;
                if (hsz > 0) {
                    heap[0] = heap[hsz];
                    sift_min_merge(heap, hsz, all_k, all_s, run_pos);
                }
            }
            if (k != last_k) {
                last_k = k;
                if (t == 0) {
                    new_k[new_len] = k;
                    new_v[new_len] = v;
                    new_len++;
                }
            }
        }

        free(l1_k);
        free(l1_v);
        l1_k = new_k;
        l1_v = new_v;
        n_l1 = new_len;
        ck = (ck * 37LL + (int64_t)n_l1) % MOD_V;

        for (int q = 0; q < 60000; q++) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t qk = rng % 40000LL;
            int lo = 0;
            int hi = n_l1;
            while (lo < hi) {
                int mid = (lo + hi) >> 1;
                if (l1_k[mid] < qk) {
                    lo = mid + 1;
                } else {
                    hi = mid;
                }
            }
            if (lo < n_l1 && l1_k[lo] == qk) {
                hits++;
                ck = (ck * 31LL + l1_v[lo]) % MOD_V;
            }
        }
    }

    printf("%" PRId64 "\n%" PRId64 "\n", hits, ck);
    free(l1_k);
    free(l1_v);
    free(rk);
    free(rs);
    free(rv);
    free(rt);
    free(all_k);
    free(all_s);
    free(all_v);
    free(all_t);
    return 0;
}
