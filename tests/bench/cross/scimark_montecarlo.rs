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
    let mut rng = SciRandom::new(113);
    let mut under: i64 = 0;
    for _ in 0..5_000_000 {
        let x = rng.next_double();
        let y = rng.next_double();
        if x * x + y * y <= 1.0 {
            under += 1;
        }
    }
    println!("{}", under);
}
