fn main() {
    const D0: usize = 64;
    const D1: usize = 128;
    const D2: usize = 64;
    const D3: usize = 16;
    let mut rng: i64 = 73737373;

    let mut w1 = vec![0.0f64; D1 * D0];
    let mut b1 = [0.0f64; D1];
    let mut w2 = vec![0.0f64; D2 * D1];
    let mut b2 = [0.0f64; D2];
    let mut w3 = vec![0.0f64; D3 * D2];
    let mut b3 = [0.0f64; D3];

    for k in 0..(D1 * D0) {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        w1[k] = ((rng % 255) - 127) as f64 / 1024.0;
    }
    for k in 0..D1 {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        b1[k] = ((rng % 63) - 31) as f64 / 256.0;
    }
    for k in 0..(D2 * D1) {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        w2[k] = ((rng % 255) - 127) as f64 / 1024.0;
    }
    for k in 0..D2 {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        b2[k] = ((rng % 63) - 31) as f64 / 256.0;
    }
    for k in 0..(D3 * D2) {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        w3[k] = ((rng % 255) - 127) as f64 / 1024.0;
    }
    for k in 0..D3 {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        b3[k] = ((rng % 63) - 31) as f64 / 256.0;
    }

    let mut x = [0.0f64; D0];
    let mut h1 = [0.0f64; D1];
    let mut h2 = [0.0f64; D2];
    let mut cls_sum: i64 = 0;
    let mut logit_acc: f64 = 0.0;

    for _smp in 0..2000 {
        for i in 0..D0 {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            x[i] = ((rng % 255) - 127) as f64 / 128.0;
        }
        for j in 0..D1 {
            let mut s = b1[j];
            let base = j * D0;
            for i in 0..D0 {
                s += x[i] * w1[base + i];
            }
            h1[j] = if s > 0.0 { s } else { 0.0 };
        }
        for j in 0..D2 {
            let mut s = b2[j];
            let base = j * D1;
            for i in 0..D1 {
                s += h1[i] * w2[base + i];
            }
            h2[j] = if s > 0.0 { s } else { 0.0 };
        }
        let mut best_c = 0usize;
        let mut best_v = -1.0e18;
        for j in 0..D3 {
            let mut s = b3[j];
            let base = j * D2;
            for i in 0..D2 {
                s += h2[i] * w3[base + i];
            }
            if s > best_v {
                best_v = s;
                best_c = j;
            }
        }
        cls_sum += best_c as i64;
        logit_acc += best_v.abs();
    }

    println!("{}\n{}", cls_sum, (logit_acc * 10.0 + 0.5).floor() as i64);
}
