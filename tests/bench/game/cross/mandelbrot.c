#include <stdio.h>
#include <stdlib.h>
int main(int argc, char **argv) {
    int N = argc>1 ? atoi(argv[1]) : 4000;
    int w = (N + 7) / 8 * 8;
    unsigned char *pix = (unsigned char*)calloc(w * w / 8, 1);
    for (int y = 0; y < w; y++) {
        double Ci = 2.0 * (double)y / (double)w - 1.0;
        for (int x = 0; x < w; x++) {
            double Cr = 2.0 * (double)x / (double)w - 1.5;
            double Zr = 0, Zi = 0, Tr = 0, Ti = 0;
            int i = 0;
            while (i < 50 && Tr + Ti <= 4.0) {
                Zi = 2.0 * Zr * Zi + Ci;
                Zr = Tr - Ti + Cr;
                Tr = Zr * Zr;
                Ti = Zi * Zi;
                i++;
            }
            if (Tr + Ti <= 4.0) {
                pix[y * (w / 8) + (x >> 3)] |= (unsigned char)(0x80 >> (x & 7));
            }
        }
    }
    printf("P4\n%d %d\n", w, w);
    fwrite(pix, 1, w * w / 8, stdout);
    return 0;
}
