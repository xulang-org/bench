#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>

#define MOD_V 1000000007LL

static int64_t isqrt64(int64_t n) {
    if (n <= 0) {
        return 0;
    }
    int64_t x = n;
    int64_t y = (x + 1) >> 1;
    while (y < x) {
        x = y;
        y = (x + n / x) >> 1;
    }
    return x;
}

static int64_t sdiv(int64_t num, int64_t den) {
    if (num >= 0) {
        return num / den;
    }
    return -((-num) / den);
}

int main(void) {
    const int n = 512;
    const int64_t arena = 65536LL;
    int64_t rng = 62626262LL;

    int64_t px[512], py[512], vx[512], vy[512], rad[512];
    int nxt_b[512];
    for (int i = 0; i < n; i++) {
        int64_t row = i / 32;
        int64_t col = i % 32;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        px[i] = 1024LL + col * 2000LL + (rng % 200LL);
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        py[i] = 1024LL + row * 4000LL + (rng % 200LL);
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        vx[i] = (rng % 321LL) - 160LL;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        vy[i] = (rng % 321LL) - 160LL;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        rad[i] = 384LL + (rng % 257LL);
        nxt_b[i] = -1;
    }

    int head[256];
    int64_t collisions = 0;

    for (int step = 0; step < 500; step++) {
        for (int c = 0; c < 256; c++) {
            head[c] = -1;
        }
        for (int i = 0; i < n; i++) {
            int64_t x = px[i] + vx[i];
            int64_t y = py[i] + vy[i];
            int64_t r = rad[i];
            if (x < r) {
                x = r;
                vx[i] = -vx[i];
            } else if (x > arena - r) {
                x = arena - r;
                vx[i] = -vx[i];
            }
            if (y < r) {
                y = r;
                vy[i] = -vy[i];
            } else if (y > arena - r) {
                y = arena - r;
                vy[i] = -vy[i];
            }
            px[i] = x;
            py[i] = y;
            int cx = (int)(x >> 12);
            int cy = (int)(y >> 12);
            if (cx > 15) cx = 15;
            if (cy > 15) cy = 15;
            int cell = (cy << 4) | cx;
            nxt_b[i] = head[cell];
            head[cell] = i;
        }

        for (int i = 0; i < n; i++) {
            int cx = (int)(px[i] >> 12);
            int cy = (int)(py[i] >> 12);
            if (cx > 15) cx = 15;
            if (cy > 15) cy = 15;
            int y0 = (cy > 0) ? (cy - 1) : 0;
            int y1 = (cy < 15) ? (cy + 1) : 15;
            int x0 = (cx > 0) ? (cx - 1) : 0;
            int x1 = (cx < 15) ? (cx + 1) : 15;
            for (int ny = y0; ny <= y1; ny++) {
                for (int nx = x0; nx <= x1; nx++) {
                    int j = head[(ny << 4) | nx];
                    while (j != -1) {
                        if (j > i) {
                            int64_t dx = px[j] - px[i];
                            int64_t dy = py[j] - py[i];
                            int64_t rsum = rad[i] + rad[j];
                            int64_t dist2 = dx * dx + dy * dy;
                            if (dist2 < rsum * rsum && dist2 > 0) {
                                collisions++;
                                int64_t dist = isqrt64(dist2);
                                if (dist < 1) dist = 1;
                                int64_t half = (rsum - dist + 1) >> 1;
                                int64_t sx = sdiv(dx * half, dist);
                                int64_t sy = sdiv(dy * half, dist);
                                px[i] -= sx;
                                py[i] -= sy;
                                px[j] += sx;
                                py[j] += sy;
                                int64_t vn = (vx[j] - vx[i]) * dx + (vy[j] - vy[i]) * dy;
                                if (vn < 0) {
                                    int64_t ix = sdiv(vn * dx, dist2);
                                    int64_t iy = sdiv(vn * dy, dist2);
                                    vx[i] += ix;
                                    vy[i] += iy;
                                    vx[j] -= ix;
                                    vy[j] -= iy;
                                }
                            }
                        }
                        j = nxt_b[j];
                    }
                }
            }
        }
    }

    int64_t ck = 0;
    for (int i = 0; i < n; i++) {
        int64_t v = (px[i] + 100000LL) * 7LL + (py[i] + 100000LL) * 13LL
            + (vx[i] + 100000LL) * 17LL + (vy[i] + 100000LL);
        ck = (ck * 31LL + (v % MOD_V)) % MOD_V;
    }

    printf("%" PRId64 "\n%" PRId64 "\n", collisions, ck);
    return 0;
}
