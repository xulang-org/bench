#include <inttypes.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>

int main(void) {
    double cx[16], cy[16], cz[16], cr[16];
    double sr[16], sg[16], sb[16], refl[16];

    cx[0] = 0.0;
    cy[0] = -1001.5;
    cz[0] = -6.0;
    cr[0] = 1000.0;
    sr[0] = 0.45;
    sg[0] = 0.48;
    sb[0] = 0.52;
    refl[0] = 0.25;

    int64_t rng = 44556677LL;
    for (int i = 1; i < 16; i++) {
        int row = (i - 1) / 5;
        int col = (i - 1) % 5;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        cx[i] = -3.2 + (double)col * 1.6 + (double)((rng % 41LL) - 20LL) / 128.0;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        cy[i] = -0.7 + (double)row * 1.1 + (double)((rng % 33LL) - 16LL) / 128.0;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        cz[i] = -4.2 - (double)row * 1.8 - (double)(rng % 33LL) / 64.0;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        cr[i] = 0.45 + (double)(rng % 17LL) / 64.0;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        sr[i] = 0.25 + (double)(rng % 48LL) / 64.0;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        sg[i] = 0.25 + (double)(rng % 48LL) / 64.0;
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        sb[i] = 0.25 + (double)(rng % 48LL) / 64.0;
        refl[i] = 0.2 + (double)(i % 4) * 0.15;
    }

    const double lx = 0.5773502691896258;
    const double ly = 0.5773502691896258;
    const double lz = 0.5773502691896258;
    const int w = 320;
    const int h = 240;
    int64_t hit_count = 0;
    double total_lum = 0.0;

    for (int py = 0; py < h; py++) {
        double v = (0.5 - ((double)py + 0.5) / 240.0) * 1.5;
        for (int px = 0; px < w; px++) {
            double u = (((double)px + 0.5) / 320.0 - 0.5) * 2.0;
            double inv_l = 1.0 / sqrt(u * u + v * v + 1.0);
            double ox = 0.0, oy = 0.2, oz = 0.0;
            double dx = u * inv_l, dy = v * inv_l, dz = -1.0 * inv_l;
            double att = 1.0;
            double pr = 0.0, pg = 0.0, pb = 0.0;

            for (int depth = 0; depth < 3; depth++) {
                double best_t = 1.0e18;
                int best_i = -1;
                for (int i = 0; i < 16; i++) {
                    double ocx = ox - cx[i];
                    double ocy = oy - cy[i];
                    double ocz = oz - cz[i];
                    double b = ocx * dx + ocy * dy + ocz * dz;
                    double c = ocx * ocx + ocy * ocy + ocz * ocz - cr[i] * cr[i];
                    double disc = b * b - c;
                    if (disc > 0.0) {
                        double t = -b - sqrt(disc);
                        if (t > 0.0005 && t < best_t) {
                            best_t = t;
                            best_i = i;
                        }
                    }
                }
                if (best_i == -1) {
                    double sky = 0.5 * (dy + 1.0);
                    pr += att * (0.2 + 0.4 * sky);
                    pg += att * (0.3 + 0.4 * sky);
                    pb += att * (0.5 + 0.4 * sky);
                    break;
                }
                hit_count++;
                double hx = ox + dx * best_t;
                double hy = oy + dy * best_t;
                double hz = oz + dz * best_t;
                double inv_r = 1.0 / cr[best_i];
                double nx = (hx - cx[best_i]) * inv_r;
                double ny = (hy - cy[best_i]) * inv_r;
                double nz = (hz - cz[best_i]) * inv_r;

                double sox = hx + nx * 0.002;
                double soy = hy + ny * 0.002;
                double soz = hz + nz * 0.002;
                int in_shadow = 0;
                for (int j = 0; j < 16; j++) {
                    double ocx = sox - cx[j];
                    double ocy = soy - cy[j];
                    double ocz = soz - cz[j];
                    double b = ocx * lx + ocy * ly + ocz * lz;
                    double c = ocx * ocx + ocy * ocy + ocz * ocz - cr[j] * cr[j];
                    double disc = b * b - c;
                    if (disc > 0.0) {
                        double st = -b - sqrt(disc);
                        if (st > 0.0005) {
                            in_shadow = 1;
                            break;
                        }
                    }
                }

                double diff = 0.0;
                double spec = 0.0;
                if (!in_shadow) {
                    double ndotl = nx * lx + ny * ly + nz * lz;
                    if (ndotl > 0.0) {
                        diff = ndotl;
                        double hx2 = lx - dx;
                        double hy2 = ly - dy;
                        double hz2 = lz - dz;
                        double hinv = 1.0 / sqrt(hx2 * hx2 + hy2 * hy2 + hz2 * hz2);
                        double ndoth = (nx * hx2 + ny * hy2 + nz * hz2) * hinv;
                        if (ndoth > 0.0) {
                            double s2 = ndoth * ndoth;
                            double s4 = s2 * s2;
                            spec = s4 * s4 * 0.5;
                        }
                    }
                }
                double shade = 0.1 + 0.75 * diff;
                double kr = refl[best_i];
                pr += att * (1.0 - kr) * (sr[best_i] * shade + spec);
                pg += att * (1.0 - kr) * (sg[best_i] * shade + spec);
                pb += att * (1.0 - kr) * (sb[best_i] * shade + spec);
                att *= kr;
                if (att < 0.02) {
                    break;
                }
                double dot2 = 2.0 * (dx * nx + dy * ny + dz * nz);
                dx -= dot2 * nx;
                dy -= dot2 * ny;
                dz -= dot2 * nz;
                ox = sox;
                oy = soy;
                oz = soz;
            }
            total_lum += pr + pg + pb;
        }
    }

    printf("%" PRId64 "\n%" PRId64 "\n", hit_count, (int64_t)floor(total_lum * 10.0 + 0.5));
    return 0;
}
