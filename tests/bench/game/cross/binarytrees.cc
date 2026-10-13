#include <stdio.h>
#include <stdlib.h>
typedef struct T { struct T *l, *r; } T;
static T *new_tree(int d) {
    T *t = (T*)malloc(sizeof(T));
    if (d > 0) { t->l = new_tree(d-1); t->r = new_tree(d-1); }
    else { t->l = t->r = NULL; }
    return t;
}
static int count(T *t) { return t->l ? 1 + count(t->l) + count(t->r) : 1; }
static void free_tree(T *t) { if (!t) return; free_tree(t->l); free_tree(t->r); free(t); }
int main(int argc, char **argv) {
    int maxDepth = argc>1 ? atoi(argv[1]) : 18;
    const int minDepth = 4;
    if (maxDepth < minDepth+2) maxDepth = minDepth+2;
    int stretch = maxDepth+1;
    T *st = new_tree(stretch);
    printf("stretch tree of depth %d\t check: %d\n", stretch, count(st));
    free_tree(st);
    T *longLived = new_tree(maxDepth);
    for (int depth=minDepth; depth<=maxDepth; depth+=2) {
        int iterations = 1 << (maxDepth - depth + minDepth);
        int check = 0;
        for (int i=0;i<iterations;i++) { T *t=new_tree(depth); check += count(t); free_tree(t); }
        printf("%d\t trees of depth %d\t check: %d\n", iterations, depth, check);
    }
    printf("long lived tree of depth %d\t check: %d\n", maxDepth, count(longLived));
    free_tree(longLived);
    return 0;
}
