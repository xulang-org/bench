#include <inttypes.h>
#include <stdio.h>

int main(void) {
    int64_t a[256];
    int64_t b[256];
    int64_t dp[512];

    int64_t rng = 987654321;
    int64_t sum_lev = 0;
    int64_t ck_lev = 0;
    for (int64_t p = 0; p < 400; p++) {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        int64_t la = 120 + (rng % 100);
        rng = (rng * 1103515245 + 12345) & 2147483647;
        int64_t lb = 120 + (rng % 100);
        for (int64_t i = 0; i < la; i++) {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            a[i] = 97 + ((rng >> 16) & 7);
        }
        for (int64_t i = 0; i < lb; i++) {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            if (i < la && (rng % 5) == 0) {
                b[i] = a[i];
            } else {
                b[i] = 97 + ((rng >> 16) & 7);
            }
        }

        for (int64_t j = 0; j <= lb; j++) {
            dp[j] = j;
        }
        for (int64_t i = 1; i <= la; i++) {
            int64_t cur_off = (i & 1) * 256;
            int64_t prev_off = 256 - cur_off;
            dp[cur_off] = i;
            int64_t ai = a[i - 1];
            for (int64_t j = 1; j <= lb; j++) {
                int64_t cost = (ai == b[j - 1]) ? 0 : 1;
                int64_t d1 = dp[prev_off + j] + 1;
                int64_t d2 = dp[cur_off + j - 1] + 1;
                int64_t d3 = dp[prev_off + j - 1] + cost;
                int64_t best = d1;
                if (d2 < best) best = d2;
                if (d3 < best) best = d3;
                dp[cur_off + j] = best;
            }
        }
        int64_t d = dp[(la & 1) * 256 + lb];
        sum_lev += d;
        ck_lev = (ck_lev * 1000003 + d) % 1000000007;
    }
    printf("%" PRId64 "\n%" PRId64 "\n", sum_lev, ck_lev);
    return 0;
}
