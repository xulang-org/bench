#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

static void qsort_hoare(int64_t *a, int64_t low, int64_t high) {
    if (low >= high) return;
    int64_t pivot = a[(low + high) / 2];
    int64_t i = low;
    int64_t j = high;
    while (i <= j) {
        while (a[i] < pivot) i++;
        while (a[j] > pivot) j--;
        if (i <= j) {
            int64_t tmp = a[i];
            a[i] = a[j];
            a[j] = tmp;
            i++;
            j--;
        }
    }
    if (low < j) qsort_hoare(a, low, j);
    if (i < high) qsort_hoare(a, i, high);
}

int main(void) {
    int64_t checksum = 0;
    int64_t *arr = (int64_t *)malloc(100000 * sizeof(int64_t));

    for (int round = 0; round < 5; round++) {
        int64_t seed = 123456789 + round * 1013904223LL;
        for (int k = 0; k < 100000; k++) {
            seed = (seed * 1664525 + 1013904223) % 2147483647;
            arr[k] = seed;
        }
        qsort_hoare(arr, 0, 99999);
        for (int i = 0; i < 100000; i++) {
            checksum = (checksum * 31 + arr[i]) % 1000000007;
        }
    }

    printf("%lld\n", (long long)checksum);
    free(arr);
    return 0;
}
