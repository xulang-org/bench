const MOD_V: i64 = 1000000007;
const PMAX: usize = 2048;
const MAX_ORD: usize = 262144;

struct OrderBook {
    b_head: [i64; PMAX],
    b_tail: [i64; PMAX],
    a_head: [i64; PMAX],
    a_tail: [i64; PMAX],
    o_side: Vec<i64>,
    o_px: Vec<usize>,
    o_qty: Vec<i64>,
    o_act: Vec<i64>,
    o_prev: Vec<i64>,
    o_next: Vec<i64>,
}

impl OrderBook {
    fn new() -> Self {
        Self {
            b_head: [-1; PMAX],
            b_tail: [-1; PMAX],
            a_head: [-1; PMAX],
            a_tail: [-1; PMAX],
            o_side: vec![0; MAX_ORD],
            o_px: vec![0; MAX_ORD],
            o_qty: vec![0; MAX_ORD],
            o_act: vec![0; MAX_ORD],
            o_prev: vec![-1; MAX_ORD],
            o_next: vec![-1; MAX_ORD],
        }
    }

    fn push_bid(&mut self, px: usize, oid: usize) {
        let t = self.b_tail[px];
        self.o_prev[oid] = t;
        self.o_next[oid] = -1;
        if t != -1 {
            self.o_next[t as usize] = oid as i64;
        } else {
            self.b_head[px] = oid as i64;
        }
        self.b_tail[px] = oid as i64;
    }

    fn push_ask(&mut self, px: usize, oid: usize) {
        let t = self.a_tail[px];
        self.o_prev[oid] = t;
        self.o_next[oid] = -1;
        if t != -1 {
            self.o_next[t as usize] = oid as i64;
        } else {
            self.a_head[px] = oid as i64;
        }
        self.a_tail[px] = oid as i64;
    }

    fn unlink_bid(&mut self, px: usize, oid: usize) {
        let pr = self.o_prev[oid];
        let nx = self.o_next[oid];
        if pr != -1 {
            self.o_next[pr as usize] = nx;
        } else {
            self.b_head[px] = nx;
        }
        if nx != -1 {
            self.o_prev[nx as usize] = pr;
        } else {
            self.b_tail[px] = pr;
        }
        self.o_prev[oid] = -1;
        self.o_next[oid] = -1;
    }

    fn unlink_ask(&mut self, px: usize, oid: usize) {
        let pr = self.o_prev[oid];
        let nx = self.o_next[oid];
        if pr != -1 {
            self.o_next[pr as usize] = nx;
        } else {
            self.a_head[px] = nx;
        }
        if nx != -1 {
            self.o_prev[nx as usize] = pr;
        } else {
            self.a_tail[px] = pr;
        }
        self.o_prev[oid] = -1;
        self.o_next[oid] = -1;
    }
}

fn main() {
    let mut ob = OrderBook::new();
    let mut rng: i64 = 70707070;

    let mut best_bid: i64 = -1;
    let mut best_ask: i64 = PMAX as i64;
    let mut next_id = 0usize;
    let mut trades: i64 = 0;
    let mut cancels: i64 = 0;
    let mut ck: i64 = 0;

    for _ev in 0..250000 {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let r = rng % 10;
        if r < 2 && next_id > 0 {
            let win = if next_id < 4096 { next_id } else { 4096 };
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let cid = next_id - 1 - (rng % win as i64) as usize;
            if ob.o_act[cid] == 1 {
                let px = ob.o_px[cid];
                if ob.o_side[cid] == 0 {
                    ob.unlink_bid(px, cid);
                    if px as i64 == best_bid && ob.b_head[px] == -1 {
                        while best_bid >= 0 && ob.b_head[best_bid as usize] == -1 {
                            best_bid -= 1;
                        }
                    }
                } else {
                    ob.unlink_ask(px, cid);
                    if px as i64 == best_ask && ob.a_head[px] == -1 {
                        while best_ask < PMAX as i64 && ob.a_head[best_ask as usize] == -1 {
                            best_ask += 1;
                        }
                    }
                }
                ob.o_act[cid] = 0;
                cancels += 1;
            }
        } else {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let side = (rng >> 16) & 1;
            let mid = if best_bid >= 0 && best_ask < PMAX as i64 {
                (best_bid + best_ask) >> 1
            } else if best_bid >= 0 {
                best_bid
            } else if best_ask < PMAX as i64 {
                best_ask
            } else {
                1024
            };
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let mut px = mid + (rng % 41) - 20;
            if px < 1 {
                px = 1;
            }
            if px > (PMAX as i64) - 2 {
                px = (PMAX as i64) - 2;
            }
            let px_u = px as usize;
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let mut qty = 1 + (rng % 50);

            if side == 0 {
                while qty > 0 && best_ask <= px {
                    let ba = best_ask as usize;
                    let oid = ob.a_head[ba] as usize;
                    let fill = if qty < ob.o_qty[oid] { qty } else { ob.o_qty[oid] };
                    qty -= fill;
                    ob.o_qty[oid] -= fill;
                    trades += 1;
                    ck = (ck * 31 + fill * 1009 + best_ask) % MOD_V;
                    if ob.o_qty[oid] == 0 {
                        ob.unlink_ask(ba, oid);
                        ob.o_act[oid] = 0;
                        if ob.a_head[ba] == -1 {
                            while best_ask < PMAX as i64 && ob.a_head[best_ask as usize] == -1 {
                                best_ask += 1;
                            }
                        }
                    }
                }
                if qty > 0 {
                    let oid = next_id;
                    next_id += 1;
                    ob.o_side[oid] = 0;
                    ob.o_px[oid] = px_u;
                    ob.o_qty[oid] = qty;
                    ob.o_act[oid] = 1;
                    ob.push_bid(px_u, oid);
                    if px > best_bid {
                        best_bid = px;
                    }
                }
            } else {
                while qty > 0 && best_bid >= px {
                    let bb = best_bid as usize;
                    let oid = ob.b_head[bb] as usize;
                    let fill = if qty < ob.o_qty[oid] { qty } else { ob.o_qty[oid] };
                    qty -= fill;
                    ob.o_qty[oid] -= fill;
                    trades += 1;
                    ck = (ck * 31 + fill * 1009 + best_bid) % MOD_V;
                    if ob.o_qty[oid] == 0 {
                        ob.unlink_bid(bb, oid);
                        ob.o_act[oid] = 0;
                        if ob.b_head[bb] == -1 {
                            while best_bid >= 0 && ob.b_head[best_bid as usize] == -1 {
                                best_bid -= 1;
                            }
                        }
                    }
                }
                if qty > 0 {
                    let oid = next_id;
                    next_id += 1;
                    ob.o_side[oid] = 1;
                    ob.o_px[oid] = px_u;
                    ob.o_qty[oid] = qty;
                    ob.o_act[oid] = 1;
                    ob.push_ask(px_u, oid);
                    if px < best_ask {
                        best_ask = px;
                    }
                }
            }
        }
    }

    ck = (ck * 37 + cancels * 17 + (best_bid + 1) * 7 + best_ask) % MOD_V;
    println!("{}\n{}", trades, ck);
}
