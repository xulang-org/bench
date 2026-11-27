const MOD_V: i64 = 1000000007;

fn main() {
    const MAX_D: i64 = 120;
    const STRIDE: usize = 241;
    const OFF: i64 = 120;

    let mut v = vec![0i64; STRIDE];
    let mut trace = vec![0i64; (MAX_D as usize + 1) * STRIDE];
    let mut a = [0i64; 200];
    let mut b = [0i64; 300];
    let mut op_type = [0i64; 600];
    let mut op_val = [0i64; 600];

    let mut rng: i64 = 20260501;
    let mut total_edits: i64 = 0;
    let mut ck: i64 = 0;

    for _pair in 0..1200 {
        let n = 200usize;
        for i in 0..n {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let val = rng & 63;
            a[i] = val;
            b[i] = val;
        }
        let mut m = n;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let nmut = 18 + (rng % 11);
        for _mi in 0..nmut {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let kind = rng % 3;
            if kind == 0 && m > 120 {
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let pos = (rng % m as i64) as usize;
                let mut p = pos;
                while p + 1 < m {
                    b[p] = b[p + 1];
                    p += 1;
                }
                m -= 1;
            } else if kind == 1 && m < 260 {
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let pos = (rng % (m as i64 + 1)) as usize;
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let nv = rng & 63;
                let mut p = m;
                while p > pos {
                    b[p] = b[p - 1];
                    p -= 1;
                }
                b[pos] = nv;
                m += 1;
            } else {
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let pos = (rng % m as i64) as usize;
                rng = (rng * 1103515245 + 12345) & 2147483647;
                b[pos] = rng & 63;
            }
        }

        v[(OFF + 1) as usize] = 0;
        let mut found_d: i64 = -1;
        for d in 0..=MAX_D {
            let tbase = (d as usize) * STRIDE;
            let mut k = -d;
            while k <= d {
                let mut x = if k == -d
                    || (k != d && v[(OFF + k - 1) as usize] < v[(OFF + k + 1) as usize])
                {
                    v[(OFF + k + 1) as usize]
                } else {
                    v[(OFF + k - 1) as usize] + 1
                };
                let mut y = x - k;
                while x < n as i64 && y < m as i64 && a[x as usize] == b[y as usize] {
                    x += 1;
                    y += 1;
                }
                v[(OFF + k) as usize] = x;
                trace[tbase + (OFF + k) as usize] = x;
                if x >= n as i64 && y >= m as i64 {
                    found_d = d;
                    break;
                }
                k += 2;
            }
            if found_d >= 0 {
                break;
            }
        }

        let mut x = n as i64;
        let mut y = m as i64;
        let mut oc = 0usize;
        let mut bd = found_d;
        while bd > 0 {
            let pbase = ((bd - 1) as usize) * STRIDE;
            let k = x - y;
            let prev_k = if k == -bd
                || (k != bd
                    && trace[pbase + (OFF + k - 1) as usize]
                        < trace[pbase + (OFF + k + 1) as usize])
            {
                k + 1
            } else {
                k - 1
            };
            let prev_x = trace[pbase + (OFF + prev_k) as usize];
            let prev_y = prev_x - prev_k;
            while x > prev_x && y > prev_y {
                op_type[oc] = 0;
                op_val[oc] = a[(x - 1) as usize];
                oc += 1;
                x -= 1;
                y -= 1;
            }
            if x == prev_x {
                op_type[oc] = 1;
                op_val[oc] = b[(y - 1) as usize];
                oc += 1;
                y -= 1;
            } else {
                op_type[oc] = 2;
                op_val[oc] = a[(x - 1) as usize];
                oc += 1;
                x -= 1;
            }
            bd -= 1;
        }
        while x > 0 && y > 0 {
            op_type[oc] = 0;
            op_val[oc] = a[(x - 1) as usize];
            oc += 1;
            x -= 1;
            y -= 1;
        }

        total_edits += found_d;
        let mut sh = found_d;
        for j in 0..oc {
            sh = (sh * 131 + op_type[j] * 67 + op_val[j]) % MOD_V;
        }
        ck = (ck * 31 + sh) % MOD_V;
    }

    println!("{}\n{}", total_edits, ck);
}
