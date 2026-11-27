#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MOD_V 1000000007LL

static void enc_cp(int64_t *out, int *slen, int64_t cp) {
    if (cp < 128) {
        out[(*slen)++] = cp;
    } else if (cp < 2048) {
        out[(*slen)++] = 192 | (cp >> 6);
        out[(*slen)++] = 128 | (cp & 63);
    } else if (cp < 65536) {
        out[(*slen)++] = 224 | (cp >> 12);
        out[(*slen)++] = 128 | ((cp >> 6) & 63);
        out[(*slen)++] = 128 | (cp & 63);
    } else {
        out[(*slen)++] = 240 | (cp >> 18);
        out[(*slen)++] = 128 | ((cp >> 12) & 63);
        out[(*slen)++] = 128 | ((cp >> 6) & 63);
        out[(*slen)++] = 128 | (cp & 63);
    }
}

int main(void) {
    int64_t rng = 246801357LL;
    int64_t *src = (int64_t *)malloc(65600U * sizeof(int64_t));
    int n = 0;

    while (n < 65520) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int64_t r = rng % 100LL;
        if (r < 38) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t k = rng % 62LL;
            int64_t cp;
            if (k < 26) cp = 65 + k;
            else if (k < 52) cp = 97 + (k - 26);
            else cp = 48 + (k - 52);
            enc_cp(src, &n, cp);
        } else if (r < 52) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t w = rng % 6LL;
            if (w == 0) enc_cp(src, &n, 32);
            else if (w == 1) enc_cp(src, &n, 9);
            else if (w == 2) enc_cp(src, &n, 10);
            else if (w == 3) enc_cp(src, &n, 13);
            else if (w == 4) enc_cp(src, &n, 160);
            else enc_cp(src, &n, 12288);
        } else if (r < 64) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t g = rng % 3LL;
            int64_t cp;
            if (g == 0) {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                cp = 192 + (rng % 62LL);
            } else if (g == 1) {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                cp = 913 + (rng % 40LL);
            } else {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                cp = 1040 + (rng % 64LL);
            }
            enc_cp(src, &n, cp);
        } else if (r < 78) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t cp;
            if ((rng & 3LL) == 0) {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                int64_t qi = rng & 3LL;
                if (qi == 0) cp = 8216;
                else if (qi == 1) cp = 8217;
                else if (qi == 2) cp = 8220;
                else cp = 8221;
            } else {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                cp = 65281 + (rng % 94LL);
            }
            enc_cp(src, &n, cp);
        } else if (r < 90) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            enc_cp(src, &n, 19968 + (rng % 512LL));
        } else if (r < 97) {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            enc_cp(src, &n, 128512 + (rng % 64LL));
        } else {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t inv = rng % 4LL;
            if (inv == 0) {
                rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
                src[n++] = 128 + (rng % 64LL);
            } else if (inv == 1) {
                src[n++] = 192;
                src[n++] = 175;
            } else if (inv == 2) {
                src[n++] = 237;
                src[n++] = 160;
                src[n++] = 128;
            } else {
                src[n++] = 244;
                src[n++] = 144;
                src[n++] = 128;
                src[n++] = 128;
            }
        }
    }

    int64_t *out_buf = (int64_t *)malloc((size_t)(n * 3) * sizeof(int64_t));
    int64_t total_out = 0;
    int64_t ck = 0;

    for (int rnd = 0; rnd < 40; rnd++) {
        int i = 0;
        int olen = 0;
        int in_ws = 1;
        while (i < n) {
            int64_t b0 = src[i];
            int64_t cp = 65533;
            int adv = 1;
            if (b0 < 128) {
                cp = b0;
                adv = 1;
            } else if (b0 >= 194 && b0 <= 223) {
                if (i + 1 < n && (src[i + 1] & 192) == 128) {
                    cp = ((b0 & 31) << 6) | (src[i + 1] & 63);
                    adv = 2;
                }
            } else if (b0 >= 224 && b0 <= 239) {
                if (i + 2 < n && (src[i + 1] & 192) == 128 && (src[i + 2] & 192) == 128) {
                    int64_t c = ((b0 & 15) << 12) | ((src[i + 1] & 63) << 6) | (src[i + 2] & 63);
                    if (c >= 2048 && (c < 55296 || c > 57343)) {
                        cp = c;
                        adv = 3;
                    }
                }
            } else if (b0 >= 240 && b0 <= 244) {
                if (i + 3 < n && (src[i + 1] & 192) == 128 && (src[i + 2] & 192) == 128 && (src[i + 3] & 192) == 128) {
                    int64_t c = ((b0 & 7) << 18) | ((src[i + 1] & 63) << 12) | ((src[i + 2] & 63) << 6) | (src[i + 3] & 63);
                    if (c >= 65536 && c <= 1114111) {
                        cp = c;
                        adv = 4;
                    }
                }
            }
            i += adv;

            if (cp == 32 || cp == 9 || cp == 10 || cp == 13 || cp == 160 || cp == 12288) {
                if (in_ws == 0) {
                    out_buf[olen++] = 32;
                    in_ws = 1;
                }
                continue;
            }
            in_ws = 0;
            if (cp >= 65281 && cp <= 65374) {
                cp -= 65248;
            }
            if (cp >= 65 && cp <= 90) {
                cp += 32;
            } else if ((cp >= 192 && cp <= 214) || (cp >= 216 && cp <= 222)) {
                cp += 32;
            } else if ((cp >= 913 && cp <= 929) || (cp >= 931 && cp <= 939)) {
                cp += 32;
            } else if (cp >= 1040 && cp <= 1071) {
                cp += 32;
            } else if (cp == 8216 || cp == 8217) {
                cp = 39;
            } else if (cp == 8220 || cp == 8221) {
                cp = 34;
            }

            if (cp < 128) {
                out_buf[olen++] = cp;
            } else if (cp < 2048) {
                out_buf[olen++] = 192 | (cp >> 6);
                out_buf[olen++] = 128 | (cp & 63);
            } else if (cp < 65536) {
                out_buf[olen++] = 224 | (cp >> 12);
                out_buf[olen++] = 128 | ((cp >> 6) & 63);
                out_buf[olen++] = 128 | (cp & 63);
            } else {
                out_buf[olen++] = 240 | (cp >> 18);
                out_buf[olen++] = 128 | ((cp >> 12) & 63);
                out_buf[olen++] = 128 | ((cp >> 6) & 63);
                out_buf[olen++] = 128 | (cp & 63);
            }
        }

        int64_t h = olen;
        for (int j = 0; j < olen; j++) {
            h = (h * 131LL + out_buf[j]) % MOD_V;
        }
        total_out += olen;
        ck = (ck * 31LL + h) % MOD_V;
    }

    printf("%" PRId64 "\n%" PRId64 "\n", total_out, ck);
    free(src);
    free(out_buf);
    return 0;
}
