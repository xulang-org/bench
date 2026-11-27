#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MOD_V 1000000007LL

int main(void) {
    const int w = 512;
    const int h = 512;
    const int total_px = w * h;

    int64_t *img = (int64_t *)malloc((size_t)total_px * sizeof(int64_t));
    int64_t *blur = (int64_t *)malloc((size_t)total_px * sizeof(int64_t));
    int64_t *edges = (int64_t *)calloc((size_t)total_px, sizeof(int64_t));

    int64_t rng = 51515151LL;
    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t v = ((x * 3 + y * 5) >> 3) & 255;
            int dx = x - 256;
            int dy = y - 256;
            if (dx * dx + dy * dy < 16384) {
                v = (v + 110LL) & 255LL;
            }
            if ((x >= 80 && x < 200 && y >= 80 && y < 220) || (((x >> 5) + (y >> 5)) % 4) == 0) {
                v = (v ^ 96LL) & 255LL;
            }
            img[y * w + x] = (v + (rng & 15LL)) & 255LL;
        }
    }

    int64_t edge_cnt = 0;
    for (int p = 0; p < 6; p++) {
        for (int x = 0; x < w; x++) {
            blur[x] = img[x];
            blur[(h - 1) * w + x] = img[(h - 1) * w + x];
        }
        for (int y = 1; y < h - 1; y++) {
            int row = y * w;
            blur[row] = img[row];
            blur[row + w - 1] = img[row + w - 1];
            for (int x = 1; x < w - 1; x++) {
                int idx = row + x;
                int64_t s = img[idx - w - 1] + 2 * img[idx - w] + img[idx - w + 1]
                    + 2 * img[idx - 1] + 4 * img[idx] + 2 * img[idx + 1]
                    + img[idx + w - 1] + 2 * img[idx + w] + img[idx + w + 1];
                blur[idx] = s >> 4;
            }
        }
        for (int y = 1; y < h - 1; y++) {
            int row = y * w;
            for (int x = 1; x < w - 1; x++) {
                int idx = row + x;
                int64_t gx = -blur[idx - w - 1] + blur[idx - w + 1]
                    - 2 * blur[idx - 1] + 2 * blur[idx + 1]
                    - blur[idx + w - 1] + blur[idx + w + 1];
                int64_t gy = -blur[idx - w - 1] - 2 * blur[idx - w] - blur[idx - w + 1]
                    + blur[idx + w - 1] + 2 * blur[idx + w] + blur[idx + w + 1];
                if (gx < 0) gx = -gx;
                if (gy < 0) gy = -gy;
                int64_t mag = gx + gy;
                if (mag > 255) mag = 255;
                edges[idx] = mag;
                if (mag >= 64) {
                    edge_cnt++;
                }
            }
        }
        for (int i = 0; i < total_px; i++) {
            img[i] = (blur[i] * 3 + edges[i]) >> 2;
        }
    }

    int64_t ck = 0;
    for (int i = 0; i < total_px; i++) {
        ck = (ck * 131LL + edges[i]) % MOD_V;
    }

    printf("%" PRId64 "\n%" PRId64 "\n", edge_cnt, ck);
    free(img);
    free(blur);
    free(edges);
    return 0;
}
