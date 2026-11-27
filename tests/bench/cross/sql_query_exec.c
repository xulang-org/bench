#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MOD_V 1000000007LL

int main(void) {
    const int n_cust = 8192;
    const int ht_cap = 16384;
    const int64_t ht_mask = 16383;
    const int n_ord = 200000;
    int64_t rng = 42424242LL;

    int64_t *cust_id = (int64_t *)malloc((size_t)n_cust * sizeof(int64_t));
    int64_t *cust_reg = (int64_t *)malloc((size_t)n_cust * sizeof(int64_t));
    int64_t *cust_tier = (int64_t *)malloc((size_t)n_cust * sizeof(int64_t));
    int64_t *ht_key = (int64_t *)malloc((size_t)ht_cap * sizeof(int64_t));
    int *ht_val = (int *)malloc((size_t)ht_cap * sizeof(int));
    for (int i = 0; i < ht_cap; i++) {
        ht_key[i] = -1;
        ht_val[i] = -1;
    }

    for (int i = 0; i < n_cust; i++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int64_t cid = 100000LL + (int64_t)i * 7LL + (rng % 5LL);
        cust_id[i] = cid;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        cust_reg[i] = rng % 16LL;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        cust_tier[i] = rng % 4LL;
        int slot = (int)(((cid * 2654435761LL) >> 16) & ht_mask);
        while (ht_key[slot] != -1) {
            slot = (slot + 1) & (int)ht_mask;
        }
        ht_key[slot] = cid;
        ht_val[slot] = i;
    }

    int64_t *ord_cid = (int64_t *)malloc((size_t)n_ord * sizeof(int64_t));
    int64_t *ord_cat = (int64_t *)malloc((size_t)n_ord * sizeof(int64_t));
    int64_t *ord_amt = (int64_t *)malloc((size_t)n_ord * sizeof(int64_t));
    int64_t *ord_status = (int64_t *)malloc((size_t)n_ord * sizeof(int64_t));

    for (int i = 0; i < n_ord; i++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        if ((rng % 20LL) < 17LL) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            ord_cid[i] = cust_id[rng % n_cust];
        } else {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            ord_cid[i] = 9000000LL + (rng % 50000LL);
        }
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        ord_cat[i] = rng % 32LL;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        ord_amt[i] = 100LL + (rng % 2000LL);
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        ord_status[i] = ((rng % 5LL) != 0) ? 1 : 0;
    }

    int64_t grp_cnt[512];
    int64_t grp_rev[512];
    int active[512];
    int64_t total_rows = 0;
    int64_t ck = 0;

    for (int rnd = 0; rnd < 16; rnd++) {
        int64_t min_amt = 350LL + (int64_t)rnd * 50LL;
        for (int b = 0; b < 512; b++) {
            grp_cnt[b] = 0;
            grp_rev[b] = 0;
        }
        for (int i = 0; i < n_ord; i++) {
            if (ord_status[i] != 1) {
                continue;
            }
            int64_t amt = ord_amt[i];
            if (amt < min_amt) {
                continue;
            }
            int64_t cid = ord_cid[i];
            int slot = (int)(((cid * 2654435761LL) >> 16) & ht_mask);
            int found = -1;
            while (ht_key[slot] != -1) {
                if (ht_key[slot] == cid) {
                    found = ht_val[slot];
                    break;
                }
                slot = (slot + 1) & (int)ht_mask;
            }
            if (found == -1) {
                continue;
            }
            int64_t tier = cust_tier[found];
            if (tier == 0) {
                continue;
            }
            int gb = (int)(cust_reg[found] * 32LL + ord_cat[i]);
            grp_cnt[gb]++;
            grp_rev[gb] += amt * tier;
            total_rows++;
        }

        int acnt = 0;
        for (int b = 0; b < 512; b++) {
            if (grp_cnt[b] > 0) {
                active[acnt++] = b;
            }
        }
        for (int i = 1; i < acnt; i++) {
            int kb = active[i];
            int64_t kr = grp_rev[kb];
            int j = i - 1;
            while (j >= 0) {
                int jb = active[j];
                int64_t jr = grp_rev[jb];
                if (jr < kr || (jr == kr && jb > kb)) {
                    active[j + 1] = jb;
                    j--;
                } else {
                    break;
                }
            }
            active[j + 1] = kb;
        }
        for (int i = 0; i < acnt; i++) {
            int gb = active[i];
            int64_t row = ((int64_t)gb * 1000003LL + grp_cnt[gb] * 97LL + (grp_rev[gb] % MOD_V)) % MOD_V;
            ck = (ck * 31LL + row) % MOD_V;
        }
    }

    printf("%" PRId64 "\n%" PRId64 "\n", total_rows, ck);
    free(cust_id);
    free(cust_reg);
    free(cust_tier);
    free(ht_key);
    free(ht_val);
    free(ord_cid);
    free(ord_cat);
    free(ord_amt);
    free(ord_status);
    return 0;
}
