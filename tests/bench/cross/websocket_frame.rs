const MOD_V: i64 = 1000000007;

fn main() {
    let mut s_fin = [0i64; 80];
    let mut s_op = [0i64; 80];
    let mut s_m0 = [0i64; 80];
    let mut s_m1 = [0i64; 80];
    let mut s_m2 = [0i64; 80];
    let mut s_m3 = [0i64; 80];
    let mut s_len = [0i64; 80];
    let mut s_seed = [0i64; 80];

    let mut rng: i64 = 987654321;
    for i in 0..80 {
        let tier = i % 4;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let ln = match tier {
            0 => 13 + (rng % 90),
            1 => 126 + (rng % 300),
            2 => 500 + (rng % 1500),
            _ => 2000 + (rng % 2048),
        };
        let fin = if (i % 5) != 0 { 1 } else { 0 };
        let op = if (i & 1) == 0 { 2 } else { 1 };
        rng = (rng * 1103515245 + 12345) & 2147483647;
        s_m0[i] = (rng >> 8) & 255;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        s_m1[i] = (rng >> 8) & 255;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        s_m2[i] = (rng >> 8) & 255;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        s_m3[i] = (rng >> 8) & 255;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        s_seed[i] = (rng >> 4) & 255;
        s_fin[i] = fin;
        s_op[i] = op;
        s_len[i] = ln;
    }

    let mut wire: Vec<i64> = Vec::with_capacity(131072);
    let mut total_bytes: i64 = 0;
    let mut ck: i64 = 0;
    for rnd in 0i64..180 {
        wire.clear();
        for idx in 0..80 {
            let fin = s_fin[idx];
            let op = s_op[idx];
            let ln = s_len[idx];
            let seed = s_seed[idx];
            let m0 = (s_m0[idx] + rnd) & 255;
            let m1 = (s_m1[idx] + idx as i64) & 255;
            let m2 = s_m2[idx];
            let m3 = s_m3[idx];

            wire.push(((fin & 1) << 7) | (op & 15));
            if ln <= 125 {
                wire.push(128 | ln);
            } else {
                wire.push(128 | 126);
                wire.push((ln >> 8) & 255);
                wire.push(ln & 255);
            }
            wire.push(m0);
            wire.push(m1);
            wire.push(m2);
            wire.push(m3);

            for j in 0..ln {
                let pb = (seed + j * 17 + rnd * 3) & 255;
                let mk = match j & 3 {
                    1 => m1,
                    2 => m2,
                    3 => m3,
                    _ => m0,
                };
                wire.push(pb ^ mk);
            }
        }

        let mut pos = 0usize;
        let wlen = wire.len();
        while pos < wlen {
            let b0 = wire[pos];
            let b1 = wire[pos + 1];
            pos += 2;
            let fin = (b0 >> 7) & 1;
            let op = b0 & 15;
            let masked = (b1 >> 7) & 1;
            let mut plen = b1 & 127;
            if plen == 126 {
                plen = (wire[pos] << 8) | wire[pos + 1];
                pos += 2;
            }
            let (mut m0, mut m1, mut m2, mut m3) = (0i64, 0i64, 0i64, 0i64);
            if masked != 0 {
                m0 = wire[pos];
                m1 = wire[pos + 1];
                m2 = wire[pos + 2];
                m3 = wire[pos + 3];
                pos += 4;
            }
            let mut fh = (fin * 17 + op) % MOD_V;
            let pu = plen as usize;
            for j in 0..pu {
                let mk = match j & 3 {
                    1 => m1,
                    2 => m2,
                    3 => m3,
                    _ => m0,
                };
                let ch = wire[pos + j] ^ mk;
                fh = (fh * 131 + ch) % MOD_V;
            }
            pos += pu;
            total_bytes += plen;
            ck = (ck * 31 + fh) % MOD_V;
        }
    }
    println!("{total_bytes}");
    println!("{ck}");
}
