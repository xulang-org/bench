#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MOD_V 1000000007LL
#define PMAX 2048
#define MAX_ORD 262144

typedef struct {
    int b_head[PMAX];
    int b_tail[PMAX];
    int a_head[PMAX];
    int a_tail[PMAX];
    int *o_side;
    int *o_px;
    int64_t *o_qty;
    int *o_act;
    int *o_prev;
    int *o_next;
} OrderBook;

static void init_book(OrderBook *ob) {
    ob->o_side = (int *)calloc(MAX_ORD, sizeof(int));
    ob->o_px = (int *)calloc(MAX_ORD, sizeof(int));
    ob->o_qty = (int64_t *)calloc(MAX_ORD, sizeof(int64_t));
    ob->o_act = (int *)calloc(MAX_ORD, sizeof(int));
    ob->o_prev = (int *)malloc(MAX_ORD * sizeof(int));
    ob->o_next = (int *)malloc(MAX_ORD * sizeof(int));
    for (int i = 0; i < PMAX; i++) {
        ob->b_head[i] = -1;
        ob->b_tail[i] = -1;
        ob->a_head[i] = -1;
        ob->a_tail[i] = -1;
    }
    for (int i = 0; i < MAX_ORD; i++) {
        ob->o_prev[i] = -1;
        ob->o_next[i] = -1;
    }
}

static void free_book(OrderBook *ob) {
    free(ob->o_side);
    free(ob->o_px);
    free(ob->o_qty);
    free(ob->o_act);
    free(ob->o_prev);
    free(ob->o_next);
}

static void push_book(OrderBook *ob, int *head, int *tail, int px, int oid) {
    int t = tail[px];
    ob->o_prev[oid] = t;
    ob->o_next[oid] = -1;
    if (t != -1) {
        ob->o_next[t] = oid;
    } else {
        head[px] = oid;
    }
    tail[px] = oid;
}

static void unlink_book(OrderBook *ob, int *head, int *tail, int px, int oid) {
    int pr = ob->o_prev[oid];
    int nx = ob->o_next[oid];
    if (pr != -1) {
        ob->o_next[pr] = nx;
    } else {
        head[px] = nx;
    }
    if (nx != -1) {
        ob->o_prev[nx] = pr;
    } else {
        tail[px] = pr;
    }
    ob->o_prev[oid] = -1;
    ob->o_next[oid] = -1;
}

int main(void) {
    OrderBook ob;
    init_book(&ob);
    int64_t rng = 70707070LL;

    int best_bid = -1;
    int best_ask = PMAX;
    int next_id = 0;
    int64_t trades = 0;
    int64_t cancels = 0;
    int64_t ck = 0;

    for (int ev = 0; ev < 250000; ev++) {
        rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
        int64_t r = rng % 10LL;
        if (r < 2 && next_id > 0) {
            int win = (next_id < 4096) ? next_id : 4096;
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int cid = next_id - 1 - (int)(rng % (int64_t)win);
            if (ob.o_act[cid] == 1) {
                int px = ob.o_px[cid];
                if (ob.o_side[cid] == 0) {
                    unlink_book(&ob, ob.b_head, ob.b_tail, px, cid);
                    if (px == best_bid && ob.b_head[px] == -1) {
                        while (best_bid >= 0 && ob.b_head[best_bid] == -1) best_bid--;
                    }
                } else {
                    unlink_book(&ob, ob.a_head, ob.a_tail, px, cid);
                    if (px == best_ask && ob.a_head[px] == -1) {
                        while (best_ask < PMAX && ob.a_head[best_ask] == -1) best_ask++;
                    }
                }
                ob.o_act[cid] = 0;
                cancels++;
            }
        } else {
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int side = (int)((rng >> 16) & 1LL);
            int mid = 1024;
            if (best_bid >= 0 && best_ask < PMAX) mid = (best_bid + best_ask) >> 1;
            else if (best_bid >= 0) mid = best_bid;
            else if (best_ask < PMAX) mid = best_ask;

            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int px = mid + (int)(rng % 41LL) - 20;
            if (px < 1) px = 1;
            if (px > PMAX - 2) px = PMAX - 2;
            rng = (rng * 1103515245LL + 12345LL) & 2147483647LL;
            int64_t qty = 1LL + (rng % 50LL);

            if (side == 0) {
                while (qty > 0 && best_ask <= px) {
                    int oid = ob.a_head[best_ask];
                    int64_t fill = (qty < ob.o_qty[oid]) ? qty : ob.o_qty[oid];
                    qty -= fill;
                    ob.o_qty[oid] -= fill;
                    trades++;
                    ck = (ck * 31LL + fill * 1009LL + (int64_t)best_ask) % MOD_V;
                    if (ob.o_qty[oid] == 0) {
                        unlink_book(&ob, ob.a_head, ob.a_tail, best_ask, oid);
                        ob.o_act[oid] = 0;
                        if (ob.a_head[best_ask] == -1) {
                            while (best_ask < PMAX && ob.a_head[best_ask] == -1) best_ask++;
                        }
                    }
                }
                if (qty > 0) {
                    int oid = next_id++;
                    ob.o_side[oid] = 0;
                    ob.o_px[oid] = px;
                    ob.o_qty[oid] = qty;
                    ob.o_act[oid] = 1;
                    push_book(&ob, ob.b_head, ob.b_tail, px, oid);
                    if (px > best_bid) best_bid = px;
                }
            } else {
                while (qty > 0 && best_bid >= px) {
                    int oid = ob.b_head[best_bid];
                    int64_t fill = (qty < ob.o_qty[oid]) ? qty : ob.o_qty[oid];
                    qty -= fill;
                    ob.o_qty[oid] -= fill;
                    trades++;
                    ck = (ck * 31LL + fill * 1009LL + (int64_t)best_bid) % MOD_V;
                    if (ob.o_qty[oid] == 0) {
                        unlink_book(&ob, ob.b_head, ob.b_tail, best_bid, oid);
                        ob.o_act[oid] = 0;
                        if (ob.b_head[best_bid] == -1) {
                            while (best_bid >= 0 && ob.b_head[best_bid] == -1) best_bid--;
                        }
                    }
                }
                if (qty > 0) {
                    int oid = next_id++;
                    ob.o_side[oid] = 1;
                    ob.o_px[oid] = px;
                    ob.o_qty[oid] = qty;
                    ob.o_act[oid] = 1;
                    push_book(&ob, ob.a_head, ob.a_tail, px, oid);
                    if (px < best_ask) best_ask = px;
                }
            }
        }
    }

    ck = (ck * 37LL + cancels * 17LL + (int64_t)(best_bid + 1) * 7LL + (int64_t)best_ask) % MOD_V;
    printf("%" PRId64 "\n%" PRId64 "\n", trades, ck);
    free_book(&ob);
    return 0;
}
