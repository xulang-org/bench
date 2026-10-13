#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define WIDTH 60
#define IM 139968
#define IA 3877
#define IC 29573
static unsigned seed = 42;
typedef struct { double p; char c; } Acid;
static void repeat_fasta(const char *alu, int count) {
    int len = (int)strlen(alu), pos = 0;
    while (count > 0) {
        int line = count < WIDTH ? count : WIDTH;
        for (int i=0;i<line;i++) { putchar(alu[pos++]); if (pos>=len) pos=0; }
        putchar('\n'); count -= line;
    }
}
static void accumulate(Acid *g, int n) { for (int i=1;i<n;i++) g[i].p += g[i-1].p; }
static void random_fasta(Acid *g, int gn, int count) {
    while (count > 0) {
        int line = count < WIDTH ? count : WIDTH;
        for (int j=0;j<line;j++) {
            seed = (seed * IA + IC) % IM;
            double r = (double)seed / IM;
            for (int k=0;k<gn;k++) if (g[k].p >= r) { putchar(g[k].c); break; }
        }
        putchar('\n'); count -= line;
    }
}
int main(int argc, char **argv) {
    int n = argc>1 ? atoi(argv[1]) : 2500000;
    const char *alu = "GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGGGAGGCCGAGGCGGGCGGATCACCTGAGGTCAGGAGTTCGAGACCAGCCTGGCCAACATGGTGAAACCCCGTCTCTACTAAAAATACAAAAATTAGCCGGGCGTGGTGGCGCGCGCCTGTAATCCCAGCTACTCGGGAGGCTGAGGCAGGAGAATCGCTTGAACCCGGGAGGCGGAGGTTGCAGTGAGCCGAGATCGCGCCACTGCACTCCAGCCTGGGCGACAGAGCGAGACTCCGTCTCAAAAA";
    Acid iub[] = {{0.27,'a'},{0.12,'c'},{0.12,'g'},{0.27,'t'},{0.02,'B'},{0.02,'D'},{0.02,'H'},{0.02,'K'},{0.02,'M'},{0.02,'N'},{0.02,'R'},{0.02,'S'},{0.02,'V'},{0.02,'W'},{0.02,'Y'}};
    Acid hs[] = {{0.3029549426680,'a'},{0.1979883004921,'c'},{0.1975473066391,'g'},{0.3015094502008,'t'}};
    accumulate(iub, 15); accumulate(hs, 4);
    printf(">ONE Homo sapiens alu\n"); repeat_fasta(alu, 2*n);
    printf(">TWO IUB ambiguity codes\n"); random_fasta(iub, 15, 3*n);
    printf(">THREE Homo sapiens frequency\n"); random_fasta(hs, 4, 5*n);
    return 0;
}
