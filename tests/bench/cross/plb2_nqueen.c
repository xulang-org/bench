#include <stdint.h>
#include <stdio.h>

static int64_t nq_solve(int n) {
    int64_t l[32] = {0}, c[32] = {0}, r[32] = {0}, m[32] = {0};
    int64_t y0 = (INT64_C(1) << n) - 1;
    int k = 0;
    m[0] = y0;
    int64_t cnt = 0;
    while (k >= 0) {
        int64_t y = m[k];
        if (y == 0) {
            k -= 1;
        } else {
            int64_t z = y & (0 - y);
            m[k] = y - z;
            if (k == n - 1) {
                cnt += 1;
            } else {
                k += 1;
                l[k] = ((l[k - 1] | z) << 1) & y0;
                c[k] = c[k - 1] | z;
                r[k] = (r[k - 1] | z) >> 1;
                m[k] = y0 ^ (l[k] | c[k] | r[k]);
            }
        }
    }
    return cnt;
}

int main(void) {
    printf("%lld\n", (long long)nq_solve(15));
    return 0;
}
