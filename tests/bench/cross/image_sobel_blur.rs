const MOD_V: i64 = 1000000007;

fn main() {
    const W: usize = 512;
    const H: usize = 512;
    const TOTAL_PX: usize = W * H;

    let mut img = vec![0i64; TOTAL_PX];
    let mut blur = vec![0i64; TOTAL_PX];
    let mut edges = vec![0i64; TOTAL_PX];

    let mut rng: i64 = 51515151;
    for y in 0..H {
        for x in 0..W {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let mut v = (((x as i64) * 3 + (y as i64) * 5) >> 3) & 255;
            let dx = x as i64 - 256;
            let dy = y as i64 - 256;
            if dx * dx + dy * dy < 16384 {
                v = (v + 110) & 255;
            }
            if (x >= 80 && x < 200 && y >= 80 && y < 220) || (((x >> 5) + (y >> 5)) % 4) == 0 {
                v = (v ^ 96) & 255;
            }
            img[y * W + x] = (v + (rng & 15)) & 255;
        }
    }

    let mut edge_cnt: i64 = 0;
    for _p in 0..6 {
        for x in 0..W {
            blur[x] = img[x];
            blur[(H - 1) * W + x] = img[(H - 1) * W + x];
        }
        for y in 1..(H - 1) {
            let row = y * W;
            blur[row] = img[row];
            blur[row + W - 1] = img[row + W - 1];
            for x in 1..(W - 1) {
                let idx = row + x;
                let s = img[idx - W - 1]
                    + 2 * img[idx - W]
                    + img[idx - W + 1]
                    + 2 * img[idx - 1]
                    + 4 * img[idx]
                    + 2 * img[idx + 1]
                    + img[idx + W - 1]
                    + 2 * img[idx + W]
                    + img[idx + W + 1];
                blur[idx] = s >> 4;
            }
        }
        for y in 1..(H - 1) {
            let row = y * W;
            for x in 1..(W - 1) {
                let idx = row + x;
                let mut gx = -blur[idx - W - 1]
                    + blur[idx - W + 1]
                    - 2 * blur[idx - 1]
                    + 2 * blur[idx + 1]
                    - blur[idx + W - 1]
                    + blur[idx + W + 1];
                let mut gy = -blur[idx - W - 1]
                    - 2 * blur[idx - W]
                    - blur[idx - W + 1]
                    + blur[idx + W - 1]
                    + 2 * blur[idx + W]
                    + blur[idx + W + 1];
                if gx < 0 {
                    gx = -gx;
                }
                if gy < 0 {
                    gy = -gy;
                }
                let mut mag = gx + gy;
                if mag > 255 {
                    mag = 255;
                }
                edges[idx] = mag;
                if mag >= 64 {
                    edge_cnt += 1;
                }
            }
        }
        for i in 0..TOTAL_PX {
            img[i] = (blur[i] * 3 + edges[i]) >> 2;
        }
    }

    let mut ck: i64 = 0;
    for i in 0..TOTAL_PX {
        ck = (ck * 131 + edges[i]) % MOD_V;
    }

    println!("{}\n{}", edge_cnt, ck);
}
