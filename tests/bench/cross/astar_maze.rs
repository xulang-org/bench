struct Heap {
    f: Vec<i64>,
    n: Vec<i64>,
    len: usize,
}

impl Heap {
    fn push(&mut self, fval: i64, node: i64) {
        let mut i = self.len;
        self.f[i] = fval;
        self.n[i] = node;
        self.len += 1;
        while i > 0 {
            let p = (i - 1) / 2;
            if self.f[p] > self.f[i] || (self.f[p] == self.f[i] && self.n[p] > self.n[i]) {
                self.f.swap(p, i);
                self.n.swap(p, i);
                i = p;
            } else {
                break;
            }
        }
    }

    fn pop(&mut self) -> i64 {
        let top = self.n[0];
        self.len -= 1;
        let sz = self.len;
        if sz > 0 {
            self.f[0] = self.f[sz];
            self.n[0] = self.n[sz];
            let mut i = 0usize;
            loop {
                let l = 2 * i + 1;
                if l >= sz {
                    break;
                }
                let r = l + 1;
                let mut best = l;
                if r < sz && (self.f[r] < self.f[l] || (self.f[r] == self.f[l] && self.n[r] < self.n[l])) {
                    best = r;
                }
                if self.f[best] < self.f[i] || (self.f[best] == self.f[i] && self.n[best] < self.n[i]) {
                    self.f.swap(i, best);
                    self.n.swap(i, best);
                    i = best;
                } else {
                    break;
                }
            }
        }
        top
    }
}

fn main() {
    const W: i64 = 81;
    const H: i64 = 81;
    const N: usize = 6561;
    const INF: i64 = 1000000000;
    const START: usize = 82;
    const GOAL: usize = 79 * 81 + 79;
    const GX: i64 = 79;
    const GY: i64 = 79;

    let mut grid = vec![1i64; N];
    let mut g_score = vec![INF; N];
    let mut closed = vec![0i64; N];
    let mut stk_x = vec![0i64; N];
    let mut stk_y = vec![0i64; N];
    let mut h = Heap {
        f: vec![0i64; 32768],
        n: vec![0i64; 32768],
        len: 0,
    };

    let dx = [0i64, 0, -2, 2];
    let dy = [-2i64, 2, 0, 0];
    let mut dirs = [0usize; 4];

    let mut sum_d: i64 = 0;
    let mut poly_d: i64 = 0;
    for m in 0i64..60 {
        let mut rng = 100003 + m * 9973;
        for i in 0..N {
            grid[i] = 1;
            g_score[i] = INF;
            closed[i] = 0;
        }
        grid[START] = 0;
        let mut sp = 1usize;
        stk_x[0] = 1;
        stk_y[0] = 1;
        while sp > 0 {
            let cx = stk_x[sp - 1];
            let cy = stk_y[sp - 1];
            let mut dc = 0usize;
            for d in 0..4 {
                let nx = cx + dx[d];
                let ny = cy + dy[d];
                if nx >= 1 && nx <= W - 2 && ny >= 1 && ny <= H - 2 && grid[(ny * W + nx) as usize] == 1 {
                    dirs[dc] = d;
                    dc += 1;
                }
            }
            if dc == 0 {
                sp -= 1;
            } else {
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let pick = dirs[(rng as usize) % dc];
                let nx = cx + dx[pick];
                let ny = cy + dy[pick];
                let mx = (cx + nx) / 2;
                let my = (cy + ny) / 2;
                grid[(my * W + mx) as usize] = 0;
                grid[(ny * W + nx) as usize] = 0;
                stk_x[sp] = nx;
                stk_y[sp] = ny;
                sp += 1;
            }
        }

        let wu = W as usize;
        for y in 1..(H as usize - 1) {
            for x in 1..(W as usize - 1) {
                let idx = y * wu + x;
                if grid[idx] == 1 {
                    if (grid[idx - 1] == 0 && grid[idx + 1] == 0) || (grid[idx - wu] == 0 && grid[idx + wu] == 0) {
                        rng = (rng * 1103515245 + 12345) & 2147483647;
                        if (rng % 100) < 12 {
                            grid[idx] = 0;
                        }
                    }
                }
            }
        }

        g_score[START] = 0;
        h.len = 0;
        h.push(156, START as i64);
        let mut ans: i64 = -1;
        while h.len > 0 {
            let u = h.pop() as usize;
            if closed[u] != 0 {
                continue;
            }
            closed[u] = 1;
            if u == GOAL {
                ans = g_score[u];
                break;
            }
            let gu = g_score[u] + 1;
            let ux = (u as i64) % W;
            let uy = (u as i64) / W;

            if uy > 0 {
                let v = u - wu;
                if grid[v] == 0 && closed[v] == 0 && gu < g_score[v] {
                    g_score[v] = gu;
                    let dh = (GX - ux).abs() + (GY - (uy - 1)).abs();
                    h.push(gu + dh, v as i64);
                }
            }
            if uy + 1 < H {
                let v = u + wu;
                if grid[v] == 0 && closed[v] == 0 && gu < g_score[v] {
                    g_score[v] = gu;
                    let dh = (GX - ux).abs() + (GY - (uy + 1)).abs();
                    h.push(gu + dh, v as i64);
                }
            }
            if ux > 0 {
                let v = u - 1;
                if grid[v] == 0 && closed[v] == 0 && gu < g_score[v] {
                    g_score[v] = gu;
                    let dh = (GX - (ux - 1)).abs() + (GY - uy).abs();
                    h.push(gu + dh, v as i64);
                }
            }
            if ux + 1 < W {
                let v = u + 1;
                if grid[v] == 0 && closed[v] == 0 && gu < g_score[v] {
                    g_score[v] = gu;
                    let dh = (GX - (ux + 1)).abs() + (GY - uy).abs();
                    h.push(gu + dh, v as i64);
                }
            }
        }
        sum_d += ans;
        poly_d = (poly_d * 1000003 + ans) % 1000000007;
    }
    println!("{}\n{}", sum_d, poly_d);
}
