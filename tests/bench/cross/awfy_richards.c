#include <inttypes.h>
#include <stdio.h>

typedef struct {
    int64_t pkt_link[8];
    int64_t pkt_id[8];
    int64_t pkt_kind[8];
    int64_t pkt_datum[8];
    int64_t pkt_data[32];
    int64_t pkt_n;
    int64_t t_link[6];
    int64_t t_pri[6];
    int64_t t_inp[6];
    int64_t t_pkt_pend[6];
    int64_t t_waiting[6];
    int64_t t_holding[6];
    int64_t t_v1[6];
    int64_t t_v2[6];
    int64_t task_list;
    int64_t queue_count;
    int64_t hold_count;
    int64_t cur;
    int64_t cur_id;
} RichardsState;

static int64_t create_pkt(RichardsState *s, int64_t link, int64_t identity, int64_t kind) {
    int64_t idx = s->pkt_n++;
    s->pkt_link[idx] = link;
    s->pkt_id[idx] = identity;
    s->pkt_kind[idx] = kind;
    s->pkt_datum[idx] = 0;
    int64_t base = idx * 4;
    s->pkt_data[base] = 0;
    s->pkt_data[base + 1] = 0;
    s->pkt_data[base + 2] = 0;
    s->pkt_data[base + 3] = 0;
    return idx;
}

static int64_t append_pkt(RichardsState *s, int64_t pkt, int64_t head) {
    s->pkt_link[pkt] = -1;
    if (head == -1) {
        return pkt;
    }
    int64_t cur = head;
    while (s->pkt_link[cur] != -1) {
        cur = s->pkt_link[cur];
    }
    s->pkt_link[cur] = pkt;
    return head;
}

static void add_task(
    RichardsState *s,
    int64_t tid,
    int64_t pri,
    int64_t inp,
    int64_t pkt_p,
    int64_t wait_f,
    int64_t hold_f,
    int64_t v1,
    int64_t v2
) {
    s->t_link[tid] = s->task_list;
    s->t_pri[tid] = pri;
    s->t_inp[tid] = inp;
    s->t_pkt_pend[tid] = pkt_p;
    s->t_waiting[tid] = wait_f;
    s->t_holding[tid] = hold_f;
    s->t_v1[tid] = v1;
    s->t_v2[tid] = v2;
    s->task_list = tid;
}

static int64_t queue_pkt(RichardsState *s, int64_t p) {
    int64_t dest = s->pkt_id[p];
    if (dest < 0 || dest >= 6) {
        return -1;
    }
    s->queue_count += 1;
    s->pkt_link[p] = -1;
    s->pkt_id[p] = s->cur_id;
    if (s->t_inp[dest] == -1) {
        s->t_inp[dest] = p;
        s->t_pkt_pend[dest] = 1;
        if (s->t_pri[dest] > s->t_pri[s->cur]) {
            return dest;
        }
    } else {
        s->t_inp[dest] = append_pkt(s, p, s->t_inp[dest]);
    }
    return s->cur;
}

static void run_richards_once(RichardsState *s) {
    s->pkt_n = 0;
    s->task_list = -1;
    s->queue_count = 0;
    s->hold_count = 0;
    s->cur_id = -1;

    add_task(s, 0, 0, -1, 0, 0, 0, 1, 10000);

    int64_t wq = create_pkt(s, -1, 1, 1);
    wq = create_pkt(s, wq, 1, 1);
    add_task(s, 1, 1000, wq, 1, 1, 0, 2, 0);

    wq = create_pkt(s, -1, 4, 0);
    wq = create_pkt(s, wq, 4, 0);
    wq = create_pkt(s, wq, 4, 0);
    add_task(s, 2, 2000, wq, 1, 1, 0, -1, -1);

    wq = create_pkt(s, -1, 5, 0);
    wq = create_pkt(s, wq, 5, 0);
    wq = create_pkt(s, wq, 5, 0);
    add_task(s, 3, 3000, wq, 1, 1, 0, -1, -1);

    add_task(s, 4, 4000, -1, 0, 1, 0, -1, 0);
    add_task(s, 5, 5000, -1, 0, 1, 0, -1, 0);

    s->cur = s->task_list;
    while (s->cur != -1) {
        int64_t c = s->cur;
        if (s->t_holding[c] != 0 || (s->t_pkt_pend[c] == 0 && s->t_waiting[c] != 0)) {
            s->cur = s->t_link[c];
            continue;
        }
        s->cur_id = c;
        int64_t msg = -1;
        if (s->t_holding[c] == 0 && s->t_waiting[c] != 0 && s->t_pkt_pend[c] != 0) {
            msg = s->t_inp[c];
            s->t_inp[c] = s->pkt_link[msg];
            s->t_pkt_pend[c] = (s->t_inp[c] == -1) ? 0 : 1;
            s->t_waiting[c] = 0;
            s->t_holding[c] = 0;
        }

        int64_t cid = s->cur_id;
        if (cid == 0) {
            s->t_v2[c] -= 1;
            if (s->t_v2[c] == 0) {
                s->hold_count += 1;
                s->t_holding[c] = 1;
                s->cur = s->t_link[c];
            } else if ((s->t_v1[c] & 1) == 0) {
                s->t_v1[c] = s->t_v1[c] >> 1;
                s->t_holding[4] = 0;
                if (s->t_pri[4] > s->t_pri[c]) {
                    s->cur = 4;
                }
            } else {
                s->t_v1[c] = (s->t_v1[c] >> 1) ^ 53256;
                s->t_holding[5] = 0;
                if (s->t_pri[5] > s->t_pri[c]) {
                    s->cur = 5;
                }
            }
        } else if (cid == 1) {
            if (msg == -1) {
                s->t_waiting[c] = 1;
            } else {
                s->t_v1[c] = (s->t_v1[c] == 2) ? 3 : 2;
                s->pkt_id[msg] = s->t_v1[c];
                s->pkt_datum[msg] = 0;
                int64_t base = msg * 4;
                for (int64_t i = 0; i < 4; i++) {
                    s->t_v2[c] += 1;
                    if (s->t_v2[c] > 26) {
                        s->t_v2[c] = 1;
                    }
                    s->pkt_data[base + i] = 64 + s->t_v2[c];
                }
                s->cur = queue_pkt(s, msg);
            }
        } else if (cid == 2 || cid == 3) {
            if (msg != -1) {
                if (s->pkt_kind[msg] == 1) {
                    s->t_v1[c] = append_pkt(s, msg, s->t_v1[c]);
                } else {
                    s->t_v2[c] = append_pkt(s, msg, s->t_v2[c]);
                }
            }
            int64_t wp = s->t_v1[c];
            if (wp == -1) {
                s->t_waiting[c] = 1;
            } else {
                int64_t cnt = s->pkt_datum[wp];
                if (cnt >= 4) {
                    s->t_v1[c] = s->pkt_link[wp];
                    s->cur = queue_pkt(s, wp);
                } else {
                    int64_t dp = s->t_v2[c];
                    if (dp == -1) {
                        s->t_waiting[c] = 1;
                    } else {
                        s->t_v2[c] = s->pkt_link[dp];
                        s->pkt_datum[dp] = s->pkt_data[wp * 4 + cnt];
                        s->pkt_datum[wp] = cnt + 1;
                        s->cur = queue_pkt(s, dp);
                    }
                }
            }
        } else {
            if (msg == -1) {
                if (s->t_v1[c] == -1) {
                    s->t_waiting[c] = 1;
                } else {
                    int64_t fp = s->t_v1[c];
                    s->t_v1[c] = -1;
                    s->cur = queue_pkt(s, fp);
                }
            } else {
                s->t_v1[c] = msg;
                s->hold_count += 1;
                s->t_holding[c] = 1;
                s->cur = s->t_link[c];
            }
        }
    }
}

int main(void) {
    RichardsState st;
    int64_t tot_q = 0;
    int64_t tot_h = 0;
    for (int64_t r = 0; r < 50; r++) {
        run_richards_once(&st);
        tot_q += st.queue_count;
        tot_h += st.hold_count;
    }
    printf("%" PRId64 "\n%" PRId64 "\n", tot_q, tot_h);
    return 0;
}
