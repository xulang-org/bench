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

fn fft_bitreverse(data: &mut [f64], n: usize) {
    let mut j = 0usize;
    for i in 0..(n - 1) {
        if i < j {
            let ii = 2 * i;
            let jj = 2 * j;
            data.swap(ii, jj);
            data.swap(ii + 1, jj + 1);
        }
        let mut k = n >> 1;
        while k <= j {
            j -= k;
            k >>= 1;
        }
        j += k;
    }
}

fn fft_transform(data: &mut [f64], n: usize, direction: f64) {
    fft_bitreverse(data, n);
    let mut dual = 1usize;
    for _ in 0..10 {
        let mut w_real = 1.0f64;
        let mut w_imag = 0.0f64;
        let theta = 2.0 * direction * std::f64::consts::PI / (2.0 * (dual as f64));
        let s = theta.sin();
        let t = (theta * 0.5).sin();
        let s2 = 2.0 * t * t;

        let mut b = 0usize;
        while b < n {
            let i = 2 * b;
            let j = 2 * (b + dual);
            let wd_real = data[j];
            let wd_imag = data[j + 1];
            data[j] = data[i] - wd_real;
            data[j + 1] = data[i + 1] - wd_imag;
            data[i] += wd_real;
            data[i + 1] += wd_imag;
            b += 2 * dual;
        }

        for a in 1..dual {
            let tmp_real = w_real - s * w_imag - s2 * w_real;
            let tmp_imag = w_imag + s * w_real - s2 * w_imag;
            w_real = tmp_real;
            w_imag = tmp_imag;
            b = 0;
            while b < n {
                let i = 2 * (b + a);
                let j = 2 * (b + a + dual);
                let z1_real = data[j];
                let z1_imag = data[j + 1];
                let wd_real = w_real * z1_real - w_imag * z1_imag;
                let wd_imag = w_real * z1_imag + w_imag * z1_real;
                data[j] = data[i] - wd_real;
                data[j + 1] = data[i + 1] - wd_imag;
                data[i] += wd_real;
                data[i + 1] += wd_imag;
                b += 2 * dual;
            }
        }
        dual *= 2;
    }
}

fn main() {
    let n = 1024usize;
    let mut rng = SciRandom::new(101010);
    let mut orig = Vec::with_capacity(2 * n);
    for _ in 0..(2 * n) {
        orig.push(rng.next_double());
    }
    let mut data = vec![0.0f64; 2 * n];
    let norm = 1.0 / (n as f64);
    let mut acc = 0.0f64;

    for rep in 0..200 {
        data.copy_from_slice(&orig);
        fft_transform(&mut data, n, -1.0);
        acc += data[0].abs() + data[1].abs() + data[2 * ((rep * 7) % 512)].abs();
        fft_transform(&mut data, n, 1.0);
        for v in data.iter_mut() {
            *v *= norm;
        }
        acc += data[2 * ((rep * 13) % 512)].abs();
    }
    println!("{}", (acc * 10.0 + 0.5).floor() as i64);
}
