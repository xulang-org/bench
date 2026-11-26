struct RichardsState {
    pkt_link: [i64; 8],
    pkt_id: [i64; 8],
    pkt_kind: [i64; 8],
    pkt_datum: [i64; 8],
    pkt_data: [i64; 32],
    pkt_n: usize,
    t_link: [i64; 6],
    t_pri: [i64; 6],
    t_inp: [i64; 6],
    t_pkt_pend: [i64; 6],
    t_waiting: [i64; 6],
    t_holding: [i64; 6],
    t_v1: [i64; 6],
    t_v2: [i64; 6],
    task_list: i64,
    queue_count: i64,
    hold_count: i64,
    cur: i64,
    cur_id: i64,
}

impl RichardsState {
    fn new() -> Self {
        Self {
            pkt_link: [-1; 8],
            pkt_id: [0; 8],
            pkt_kind: [0; 8],
            pkt_datum: [0; 8],
            pkt_data: [0; 32],
            pkt_n: 0,
            t_link: [-1; 6],
            t_pri: [0; 6],
            t_inp: [-1; 6],
            t_pkt_pend: [0; 6],
            t_waiting: [0; 6],
            t_holding: [0; 6],
            t_v1: [0; 6],
            t_v2: [0; 6],
            task_list: -1,
            queue_count: 0,
            hold_count: 0,
            cur: -1,
            cur_id: -1,
        }
    }

    fn create_pkt(&mut self, link: i64, identity: i64, kind: i64) -> i64 {
        let idx = self.pkt_n;
        self.pkt_n += 1;
        self.pkt_link[idx] = link;
        self.pkt_id[idx] = identity;
        self.pkt_kind[idx] = kind;
        self.pkt_datum[idx] = 0;
        let base = idx * 4;
        self.pkt_data[base] = 0;
        self.pkt_data[base + 1] = 0;
        self.pkt_data[base + 2] = 0;
        self.pkt_data[base + 3] = 0;
        idx as i64
    }

    fn append_pkt(&mut self, pkt: i64, head: i64) -> i64 {
        self.pkt_link[pkt as usize] = -1;
        if head == -1 {
            return pkt;
        }
        let mut cur = head;
        while self.pkt_link[cur as usize] != -1 {
            cur = self.pkt_link[cur as usize];
        }
        self.pkt_link[cur as usize] = pkt;
        head
    }

    #[allow(clippy::too_many_arguments)]
    fn add_task(
        &mut self,
        tid: usize,
        pri: i64,
        inp: i64,
        pkt_p: i64,
        wait_f: i64,
        hold_f: i64,
        v1: i64,
        v2: i64,
    ) {
        self.t_link[tid] = self.task_list;
        self.t_pri[tid] = pri;
        self.t_inp[tid] = inp;
        self.t_pkt_pend[tid] = pkt_p;
        self.t_waiting[tid] = wait_f;
        self.t_holding[tid] = hold_f;
        self.t_v1[tid] = v1;
        self.t_v2[tid] = v2;
        self.task_list = tid as i64;
    }

    fn queue_pkt(&mut self, p: i64) -> i64 {
        let pu = p as usize;
        let dest = self.pkt_id[pu];
        if dest < 0 || dest >= 6 {
            return -1;
        }
        let du = dest as usize;
        self.queue_count += 1;
        self.pkt_link[pu] = -1;
        self.pkt_id[pu] = self.cur_id;
        if self.t_inp[du] == -1 {
            self.t_inp[du] = p;
            self.t_pkt_pend[du] = 1;
            if self.t_pri[du] > self.t_pri[self.cur as usize] {
                return dest;
            }
        } else {
            let head = self.t_inp[du];
            self.t_inp[du] = self.append_pkt(p, head);
        }
        self.cur
    }

    fn run_once(&mut self) {
        self.pkt_n = 0;
        self.task_list = -1;
        self.queue_count = 0;
        self.hold_count = 0;
        self.cur_id = -1;

        self.add_task(0, 0, -1, 0, 0, 0, 1, 10000);

        let mut wq = self.create_pkt(-1, 1, 1);
        wq = self.create_pkt(wq, 1, 1);
        self.add_task(1, 1000, wq, 1, 1, 0, 2, 0);

        wq = self.create_pkt(-1, 4, 0);
        wq = self.create_pkt(wq, 4, 0);
        wq = self.create_pkt(wq, 4, 0);
        self.add_task(2, 2000, wq, 1, 1, 0, -1, -1);

        wq = self.create_pkt(-1, 5, 0);
        wq = self.create_pkt(wq, 5, 0);
        wq = self.create_pkt(wq, 5, 0);
        self.add_task(3, 3000, wq, 1, 1, 0, -1, -1);

        self.add_task(4, 4000, -1, 0, 1, 0, -1, 0);
        self.add_task(5, 5000, -1, 0, 1, 0, -1, 0);

        self.cur = self.task_list;
        while self.cur != -1 {
            let c = self.cur as usize;
            if self.t_holding[c] != 0 || (self.t_pkt_pend[c] == 0 && self.t_waiting[c] != 0) {
                self.cur = self.t_link[c];
                continue;
            }
            self.cur_id = self.cur;
            let mut msg: i64 = -1;
            if self.t_holding[c] == 0 && self.t_waiting[c] != 0 && self.t_pkt_pend[c] != 0 {
                msg = self.t_inp[c];
                let next_p = self.pkt_link[msg as usize];
                self.t_inp[c] = next_p;
                self.t_pkt_pend[c] = if next_p == -1 { 0 } else { 1 };
                self.t_waiting[c] = 0;
                self.t_holding[c] = 0;
            }

            let cid = self.cur_id;
            if cid == 0 {
                self.t_v2[c] -= 1;
                if self.t_v2[c] == 0 {
                    self.hold_count += 1;
                    self.t_holding[c] = 1;
                    self.cur = self.t_link[c];
                } else if (self.t_v1[c] & 1) == 0 {
                    self.t_v1[c] >>= 1;
                    self.t_holding[4] = 0;
                    if self.t_pri[4] > self.t_pri[c] {
                        self.cur = 4;
                    }
                } else {
                    self.t_v1[c] = (self.t_v1[c] >> 1) ^ 53256;
                    self.t_holding[5] = 0;
                    if self.t_pri[5] > self.t_pri[c] {
                        self.cur = 5;
                    }
                }
            } else if cid == 1 {
                if msg == -1 {
                    self.t_waiting[c] = 1;
                } else {
                    self.t_v1[c] = if self.t_v1[c] == 2 { 3 } else { 2 };
                    let mu = msg as usize;
                    self.pkt_id[mu] = self.t_v1[c];
                    self.pkt_datum[mu] = 0;
                    let base = mu * 4;
                    for i in 0..4 {
                        self.t_v2[c] += 1;
                        if self.t_v2[c] > 26 {
                            self.t_v2[c] = 1;
                        }
                        self.pkt_data[base + i] = 64 + self.t_v2[c];
                    }
                    self.cur = self.queue_pkt(msg);
                }
            } else if cid == 2 || cid == 3 {
                if msg != -1 {
                    if self.pkt_kind[msg as usize] == 1 {
                        let h = self.t_v1[c];
                        self.t_v1[c] = self.append_pkt(msg, h);
                    } else {
                        let h = self.t_v2[c];
                        self.t_v2[c] = self.append_pkt(msg, h);
                    }
                }
                let wp = self.t_v1[c];
                if wp == -1 {
                    self.t_waiting[c] = 1;
                } else {
                    let wpu = wp as usize;
                    let cnt = self.pkt_datum[wpu];
                    if cnt >= 4 {
                        self.t_v1[c] = self.pkt_link[wpu];
                        self.cur = self.queue_pkt(wp);
                    } else {
                        let dp = self.t_v2[c];
                        if dp == -1 {
                            self.t_waiting[c] = 1;
                        } else {
                            let dpu = dp as usize;
                            self.t_v2[c] = self.pkt_link[dpu];
                            self.pkt_datum[dpu] = self.pkt_data[wpu * 4 + (cnt as usize)];
                            self.pkt_datum[wpu] = cnt + 1;
                            self.cur = self.queue_pkt(dp);
                        }
                    }
                }
            } else if msg == -1 {
                if self.t_v1[c] == -1 {
                    self.t_waiting[c] = 1;
                } else {
                    let fp = self.t_v1[c];
                    self.t_v1[c] = -1;
                    self.cur = self.queue_pkt(fp);
                }
            } else {
                self.t_v1[c] = msg;
                self.hold_count += 1;
                self.t_holding[c] = 1;
                self.cur = self.t_link[c];
            }
        }
    }
}

fn main() {
    let mut st = RichardsState::new();
    let mut tot_q: i64 = 0;
    let mut tot_h: i64 = 0;
    for _ in 0..50 {
        st.run_once();
        tot_q += st.queue_count;
        tot_h += st.hold_count;
    }
    println!("{}\n{}", tot_q, tot_h);
}
