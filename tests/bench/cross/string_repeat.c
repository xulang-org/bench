#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Each iteration owns a fresh result, like the other language ports.
int main(void) {
    const char *seed = "alpha,beta,gamma,delta;omega,phi,chi;lambda,mu,nu";
    size_t width = strlen(seed);
    int64_t total = 0;
    for (int i = 0; i < 25000; ++i) {
        size_t n = width * (384 + (i & 1));
        char *out = malloc(n);
        if (!out) return 1;
        memcpy(out, seed, width);
        size_t filled = width;
        while (filled < n) {
            size_t chunk = n - filled;
            if (chunk > filled) chunk = filled;
            memcpy(out + filled, out, chunk);
            filled += chunk;
        }
        // Make the completed buffer observable to the optimizer.
        __asm__ volatile("" : : "r"(out) : "memory");
        total += (int64_t)n + (unsigned char)out[100];
        free(out);
    }
    printf("%lld\n", (long long)total);
    return 0;
}
