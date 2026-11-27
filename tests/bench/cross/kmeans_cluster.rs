const MOD_V: i64 = 1000000007;

fn main() {
    const N: usize = 8192;
    const D: usize = 8;
    const K: usize = 16;
    let mut rng: i64 = 84848484;

    let mut gt = [0.0f64; K * D];
    for c in 0..(K * D) {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        gt[c] = ((rng % 1000) - 500) as f64 / 16.0;
    }

    let mut pts = vec![0.0f64; N * D];
    let mut assign = vec![0usize; N];
    for i in 0..N {
        let g = i & 15;
        for dim in 0..D {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            pts[i * D + dim] = gt[g * D + dim] + ((rng % 129) - 64) as f64 / 32.0;
        }
    }

    let mut cent = [0.0f64; K * D];
    let mut sum_c = [0.0f64; K * D];
    cent.copy_from_slice(&pts[..(K * D)]);
    let mut cnt = [0i64; K];
    let mut final_inertia = 0.0;

    for _it in 0..25 {
        for c in 0..(K * D) {
            sum_c[c] = 0.0;
        }
        for c in 0..K {
            cnt[c] = 0;
        }
        let mut inertia = 0.0;
        for i in 0..N {
            let pb = i * D;
            let mut best_c = 0usize;
            let mut best_d = 1.0e18;
            for c in 0..K {
                let cb = c * D;
                let mut dist = 0.0;
                for dim in 0..D {
                    let diff = pts[pb + dim] - cent[cb + dim];
                    dist += diff * diff;
                }
                if dist < best_d {
                    best_d = dist;
                    best_c = c;
                }
            }
            assign[i] = best_c;
            cnt[best_c] += 1;
            inertia += best_d;
            let cb = best_c * D;
            for dim in 0..D {
                sum_c[cb + dim] += pts[pb + dim];
            }
        }
        for c in 0..K {
            if cnt[c] > 0 {
                let inv = 1.0 / (cnt[c] as f64);
                let cb = c * D;
                for dim in 0..D {
                    cent[cb + dim] = sum_c[cb + dim] * inv;
                }
            }
        }
        final_inertia = inertia;
    }

    let mut ack: i64 = 0;
    for i in 0..N {
        ack = (ack * 31 + assign[i] as i64 + 1) % MOD_V;
    }

    println!("{}\n{}", ack, (final_inertia + 0.5).floor() as i64);
}
