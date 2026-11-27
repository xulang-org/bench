const MOD_V: i64 = 1000000007;
const MAX_NODES: usize = 131072;

struct Wheel {
    t_exp: Vec<i64>,
    t_per: Vec<i64>,
    t_rep: Vec<i64>,
    t_pay: Vec<i64>,
    t_st: Vec<i64>,
    t_prev: Vec<i64>,
    t_next: Vec<i64>,
    t_bkt: Vec<i64>,
    b_head: [i64; 512],
    b_tail: [i64; 512],
    free_stack: Vec<i64>,
    free_top: usize,
}

impl Wheel {
    fn new() -> Self {
        let mut free_stack = vec![0i64; MAX_NODES];
        for i in 0..MAX_NODES {
            free_stack[i] = (MAX_NODES - 1 - i) as i64;
        }
        Self {
            t_exp: vec![0i64; MAX_NODES],
            t_per: vec![0i64; MAX_NODES],
            t_rep: vec![0i64; MAX_NODES],
            t_pay: vec![0i64; MAX_NODES],
            t_st: vec![0i64; MAX_NODES],
            t_prev: vec![-1i64; MAX_NODES],
            t_next: vec![-1i64; MAX_NODES],
            t_bkt: vec![-1i64; MAX_NODES],
            b_head: [-1i64; 512],
            b_tail: [-1i64; 512],
            free_stack,
            free_top: MAX_NODES,
        }
    }

    fn bkt_push(&mut self, b: usize, u: usize) {
        let tail = self.b_tail[b];
        self.t_prev[u] = tail;
        self.t_next[u] = -1;
        self.t_bkt[u] = b as i64;
        if tail != -1 {
            self.t_next[tail as usize] = u as i64;
        } else {
            self.b_head[b] = u as i64;
        }
        self.b_tail[b] = u as i64;
    }

    fn bkt_remove(&mut self, u: usize) {
        let b = self.t_bkt[u] as usize;
        let pr = self.t_prev[u];
        let nx = self.t_next[u];
        if pr != -1 {
            self.t_next[pr as usize] = nx;
        } else {
            self.b_head[b] = nx;
        }
        if nx != -1 {
            self.t_prev[nx as usize] = pr;
        } else {
            self.b_tail[b] = pr;
        }
        self.t_prev[u] = -1;
        self.t_next[u] = -1;
        self.t_bkt[u] = -1;
    }

    fn schedule_node(&mut self, u: usize, exp: i64, now: i64) {
        self.t_exp[u] = exp;
        self.t_st[u] = 1;
        if (exp - now) < 256 {
            self.bkt_push((exp & 255) as usize, u);
        } else {
            self.bkt_push(256 + ((exp >> 8) & 255) as usize, u);
        }
    }
}

fn main() {
    const RING_H: usize = 16384;
    let mut w = Wheel::new();
    let mut rng: i64 = 888777666;
    let mut handles = [-1i64; RING_H];
    let mut h_wr = 0usize;
    let mut fired: i64 = 0;
    let mut canceled: i64 = 0;
    let mut ck: i64 = 0;

    for now in 0i64..160000 {
        for _ in 0..3 {
            if w.free_top > 0 {
                w.free_top -= 1;
                let u = w.free_stack[w.free_top] as usize;
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let delay = if (rng % 10) < 6 {
                    rng = (rng * 1103515245 + 12345) & 2147483647;
                    1 + (rng % 250)
                } else {
                    rng = (rng * 1103515245 + 12345) & 2147483647;
                    256 + (rng % 4096)
                };
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let mut per: i64 = 0;
                let mut rep: i64 = 0;
                if (rng % 5) == 0 {
                    rng = (rng * 1103515245 + 12345) & 2147483647;
                    per = 17 + (rng % 200);
                    rep = 2;
                }
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let pay = rng % 100000;
                w.t_per[u] = per;
                w.t_rep[u] = rep;
                w.t_pay[u] = pay;
                w.schedule_node(u, now + delay, now);
                handles[h_wr] = u as i64;
                h_wr = (h_wr + 1) & 16383;
            }
        }

        rng = (rng * 1103515245 + 12345) & 2147483647;
        let ci = (rng & 16383) as usize;
        let cu = handles[ci];
        if cu != -1 && w.t_st[cu as usize] == 1 {
            let cu_u = cu as usize;
            w.bkt_remove(cu_u);
            w.t_st[cu_u] = 0;
            w.free_stack[w.free_top] = cu;
            w.free_top += 1;
            handles[ci] = -1;
            canceled += 1;
        }

        let tick = now + 1;
        if (tick & 255) == 0 {
            let cb = 256 + ((tick >> 8) & 255) as usize;
            let mut u = w.b_head[cb];
            w.b_head[cb] = -1;
            w.b_tail[cb] = -1;
            while u != -1 {
                let uu = u as usize;
                let nx = w.t_next[uu];
                w.t_prev[uu] = -1;
                w.t_next[uu] = -1;
                w.t_bkt[uu] = -1;
                let b = (w.t_exp[uu] & 255) as usize;
                w.bkt_push(b, uu);
                u = nx;
            }
        }

        let b0 = (tick & 255) as usize;
        let mut u = w.b_head[b0];
        w.b_head[b0] = -1;
        w.b_tail[b0] = -1;
        while u != -1 {
            let uu = u as usize;
            let nx = w.t_next[uu];
            w.t_prev[uu] = -1;
            w.t_next[uu] = -1;
            w.t_bkt[uu] = -1;
            fired += 1;
            ck = (ck * 31 + w.t_pay[uu] * 7 + tick) % MOD_V;
            if w.t_rep[uu] > 0 {
                w.t_rep[uu] -= 1;
                let next_exp = tick + w.t_per[uu];
                w.schedule_node(uu, next_exp, tick);
            } else {
                w.t_st[uu] = 0;
                w.free_stack[w.free_top] = u;
                w.free_top += 1;
            }
            u = nx;
        }
    }

    ck = (ck * 37 + canceled) % MOD_V;
    println!("{}\n{}", fired, ck);
}
