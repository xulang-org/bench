struct SciRandom {
    m: [i64; 17],
    idx_i: usize,
    idx_j: usize,
}

impl SciRandom {
    fn new(seed: i64) -> Self {
        const M1: i64 = 2147483647;
        const M2: i64 = 65536;
        let mut m = [0i64; 17];
        let mut jseed = if seed < 0 { -seed } else { seed };
        if jseed > M1 {
            jseed = M1;
        }
        if jseed % 2 == 0 {
            jseed -= 1;
        }
        let k0 = 9069 % M2;
        let k1 = 9069 / M2;
        let mut j0 = jseed % M2;
        let mut j1 = jseed / M2;
        for slot in m.iter_mut() {
            jseed = j0 * k0;
            j1 = (jseed / M2 + j0 * k1 + j1 * k0) % (M2 / 2);
            j0 = jseed % M2;
            *slot = j0 + M2 * j1;
        }
        SciRandom { m, idx_i: 4, idx_j: 16 }
    }

    #[inline(always)]
    fn next_double(&mut self) -> f64 {
        const M1: i64 = 2147483647;
        const DM1: f64 = 1.0 / 2147483647.0;
        let mut k = self.m[self.idx_i] - self.m[self.idx_j];
        if k < 0 {
            k += M1;
        }
        self.m[self.idx_j] = k;
        self.idx_i = if self.idx_i == 0 { 16 } else { self.idx_i - 1 };
        self.idx_j = if self.idx_j == 0 { 16 } else { self.idx_j - 1 };
        DM1 * (k as f64)
    }
}

fn main() {
    let n = 100usize;
    let mut rng = SciRandom::new(101010);
    let mut g = Vec::with_capacity(n * n);
    for _ in 0..(n * n) {
        g.push(rng.next_double());
    }

    let omega = 1.25f64;
    let omega_over_four = omega * 0.25;
    let one_minus_omega = 1.0 - omega;
    for _ in 0..500 {
        for i in 1..(n - 1) {
            let row = i * n;
            let up = (i - 1) * n;
            let dn = (i + 1) * n;
            for j in 1..(n - 1) {
                g[row + j] = omega_over_four * (g[up + j] + g[dn + j] + g[row + j - 1] + g[row + j + 1])
                    + one_minus_omega * g[row + j];
            }
        }
    }

    let mut total = 0.0f64;
    for &v in g.iter() {
        total += v;
    }
    println!("{}", (total * 1000.0 + 0.5).floor() as i64);
}
