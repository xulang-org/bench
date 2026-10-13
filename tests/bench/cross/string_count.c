#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
int main(void) {
    unsigned char *pool[32]; int64_t lengths[32];
    for (int64_t si=0; si<32; ++si) {
        int64_t n=8+si%24; lengths[si]=n; pool[si]=malloc((size_t)n);
        for (int64_t j=0; j<n; ++j) pool[si][j]=(unsigned char)(97+(j+si)%3);
    }
    int64_t state=1,total=0,i=0;
    while (i<1000000) {
        state=(state*1103515245+12345)&2147483647;
        int64_t idx=(state>>16)&31; unsigned char needle=(unsigned char)(97+((state>>8)&1));
        const unsigned char *s=pool[idx]; int64_t n=lengths[idx],count=0,j=0;
        while (j<n) { count += s[j]==needle; ++j; }
        total+=count; ++i;
    }
    printf("%lld\n",(long long)total);
    for (int64_t si=0; si<32; ++si) free(pool[si]);
    return 0;
}
