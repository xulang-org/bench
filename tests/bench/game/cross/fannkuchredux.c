#include <stdio.h>
#include <stdlib.h>
int main(int argc, char **argv) {
    int n = argc>1 ? atoi(argv[1]) : 12;
    int *perm1 = calloc(n, sizeof(int));
    int *count = calloc(n, sizeof(int));
    int *perm = calloc(n, sizeof(int));
    for (int i=0;i<n;i++) perm1[i]=i;
    int maxFlips=0, checksum=0, sign=1, r=n;
    for (;;) {
        while (r != 1) { count[r-1]=r; r--; }
        for (int i=0;i<n;i++) perm[i]=perm1[i];
        int flips=0, k=perm[0];
        while (k) {
            for (int i=0,j=k;i<j;i++,j--) { int t=perm[i]; perm[i]=perm[j]; perm[j]=t; }
            flips++; k=perm[0];
        }
        if (flips>maxFlips) maxFlips=flips;
        checksum += sign*flips; sign = -sign;
        for (;;) {
            if (r==n) { printf("%d\nPfannkuchen(%d) = %d\n", checksum, n, maxFlips); return 0; }
            int p0=perm1[0];
            for (int i=0;i<r;i++) perm1[i]=perm1[i+1];
            perm1[r]=p0;
            if (--count[r] > 0) break;
            r++;
        }
    }
}
