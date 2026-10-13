#include <stdint.h>
#include <stdio.h>

int main(void) {
    int64_t s = 0;
    int64_t i = 0;
    while (i < 24000000) {
        switch (i & 7) {
        case 0:
            s += 1;
            break;
        case 1:
            s += 3;
            break;
        case 2:
            s += 5;
            break;
        case 3:
            s += 7;
            break;
        case 4:
            s += 11;
            break;
        case 5:
            s += 13;
            break;
        case 6:
            s += 17;
            break;
        default:
            s += 19;
            break;
        }
        i += 1;
    }
    printf("%lld\n", (long long)s);
    printf("%lld\n", (long long)i);
    return 0;
}
