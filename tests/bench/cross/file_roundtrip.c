#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { N = 524288, ROUNDS = 32 };

int main(void) {
    unsigned char *payload = malloc(N);
    unsigned char *got = malloc(N);
    if (!payload || !got) return 1;
    memset(payload, 'A', N);
    int64_t sum = 0;
    for (int round = 0; round < ROUNDS; round += 1) {
        FILE *out = fopen("roundtrip.bin", "wb");
        if (!out || fwrite(payload, 1, N, out) != N || fclose(out) != 0) return 1;
        FILE *in = fopen("roundtrip.bin", "rb");
        if (!in || fread(got, 1, N, in) != N || fclose(in) != 0) return 1;
        if (memcmp(payload, got, N) != 0) return 1;
        sum += got[0] + got[N / 2] + got[N - 1];
    }
    printf("%lld\n", (long long)sum);
    free(got);
    free(payload);
    return 0;
}
