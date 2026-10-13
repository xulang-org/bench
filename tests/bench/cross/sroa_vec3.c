#include <stdio.h>
#include <stdint.h>

typedef struct {
    double x;
    double y;
    double z;
} Vec3;

int main(void) {
    Vec3 v[256];
    int64_t i = 0;
    while (i < 256) {
        v[i].x = (double)(i & 7);
        v[i].y = (double)((i * 3) & 7);
        v[i].z = (double)((i * 5) & 7);
        i += 1;
    }
    double acc = 0.0;
    int64_t t = 0;
    while (t < 40000) {
        i = 0;
        while (i < 256) {
            acc += v[i].x * v[i].x + v[i].y * v[i].y + v[i].z * v[i].z;
            i += 1;
        }
        t += 1;
    }
    printf("%lld\n", (long long)(int64_t)acc);
    return 0;
}
