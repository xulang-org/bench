// Osprey (MIT): benchmarks/cases/textstats; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int64_t hash_at(int64_t seed, int64_t i) {
    return (((seed + i) * 16807) % 2147483647 * 16807) % 2147483647;
}

static const char *word(int64_t k) {
    if (k == 0) { return "the"; }
    if (k == 1) { return "quick"; }
    if (k == 2) { return "brown"; }
    if (k == 3) { return "fox"; }
    if (k == 4) { return "jumps"; }
    if (k == 5) { return "over"; }
    if (k == 6) { return "lazy"; }
    return "dog";
}

static int64_t score(const char *w) {
    int64_t result = (int64_t)strlen(w);
    if (strchr(w, 'o')) { result += 7; }
    if (w[0] == 't') { result += 3; }
    return result;
}

int main(void) {
    int64_t result = 0;
    int64_t i = 0;
    while (i < 200000) {
        result += score(word(hash_at(1, i) % 8));
        i += 1;
    }
    printf("%lld\n", (long long)result);
    return 0;
}
