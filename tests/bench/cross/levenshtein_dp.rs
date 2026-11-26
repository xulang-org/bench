fn main() {
    let mut a = [0i64; 256];
    let mut b = [0i64; 256];
    let mut dp = [0i64; 512];

    let mut rng: i64 = 987654321;
    let mut sum_lev: i64 = 0;
    let mut ck_lev: i64 = 0;
    for _ in 0..400 {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let la = (120 + (rng % 100)) as usize;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let lb = (120 + (rng % 100)) as usize;
        for i in 0..la {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            a[i] = 97 + ((rng >> 16) & 7);
        }
        for i in 0..lb {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            if i < la && (rng % 5) == 0 {
                b[i] = a[i];
            } else {
                b[i] = 97 + ((rng >> 16) & 7);
            }
        }

        for j in 0..=lb {
            dp[j] = j as i64;
        }
        for i in 1..=la {
            let cur_off = (i & 1) * 256;
            let prev_off = 256 - cur_off;
            dp[cur_off] = i as i64;
            let ai = a[i - 1];
            for j in 1..=lb {
                let cost = if ai == b[j - 1] { 0 } else { 1 };
                let d1 = dp[prev_off + j] + 1;
                let d2 = dp[cur_off + j - 1] + 1;
                let d3 = dp[prev_off + j - 1] + cost;
                let mut best = d1;
                if d2 < best {
                    best = d2;
                }
                if d3 < best {
                    best = d3;
                }
                dp[cur_off + j] = best;
            }
        }
        let d = dp[(la & 1) * 256 + lb];
        sum_lev += d;
        ck_lev = (ck_lev * 1000003 + d) % 1000000007;
    }
    println!("{}\n{}", sum_lev, ck_lev);
}
