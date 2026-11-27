const MOD_V: i64 = 1000000007;

fn isqrt64(n: i64) -> i64 {
    if n <= 0 {
        return 0;
    }
    let mut x = n;
    let mut y = (x + 1) >> 1;
    while y < x {
        x = y;
        y = (x + n / x) >> 1;
    }
    x
}

fn sdiv(num: i64, den: i64) -> i64 {
    if num >= 0 {
        num / den
    } else {
        -((-num) / den)
    }
}

fn main() {
    const N: usize = 512;
    const ARENA: i64 = 65536;
    let mut rng: i64 = 62626262;

    let mut px = [0i64; N];
    let mut py = [0i64; N];
    let mut vx = [0i64; N];
    let mut vy = [0i64; N];
    let mut rad = [0i64; N];
    let mut nxt_b = [-1i64; N];

    for i in 0..N {
        let row = (i / 32) as i64;
        let col = (i % 32) as i64;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        px[i] = 1024 + col * 2000 + (rng % 200);
        rng = (rng * 1103515245 + 12345) & 2147483647;
        py[i] = 1024 + row * 4000 + (rng % 200);
        rng = (rng * 1103515245 + 12345) & 2147483647;
        vx[i] = (rng % 321) - 160;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        vy[i] = (rng % 321) - 160;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        rad[i] = 384 + (rng % 257);
    }

    let mut head = [-1i64; 256];
    let mut collisions: i64 = 0;

    for _step in 0..500 {
        for c in 0..256 {
            head[c] = -1;
        }
        for i in 0..N {
            let mut x = px[i] + vx[i];
            let mut y = py[i] + vy[i];
            let r = rad[i];
            if x < r {
                x = r;
                vx[i] = -vx[i];
            } else if x > ARENA - r {
                x = ARENA - r;
                vx[i] = -vx[i];
            }
            if y < r {
                y = r;
                vy[i] = -vy[i];
            } else if y > ARENA - r {
                y = ARENA - r;
                vy[i] = -vy[i];
            }
            px[i] = x;
            py[i] = y;
            let mut cx = (x >> 12) as usize;
            let mut cy = (y >> 12) as usize;
            if cx > 15 {
                cx = 15;
            }
            if cy > 15 {
                cy = 15;
            }
            let cell = (cy << 4) | cx;
            nxt_b[i] = head[cell];
            head[cell] = i as i64;
        }

        for i in 0..N {
            let mut cx = (px[i] >> 12) as usize;
            let mut cy = (py[i] >> 12) as usize;
            if cx > 15 {
                cx = 15;
            }
            if cy > 15 {
                cy = 15;
            }
            let y0 = if cy > 0 { cy - 1 } else { 0 };
            let y1 = if cy < 15 { cy + 1 } else { 15 };
            let x0 = if cx > 0 { cx - 1 } else { 0 };
            let x1 = if cx < 15 { cx + 1 } else { 15 };
            for ny in y0..=y1 {
                for nx in x0..=x1 {
                    let mut j_i = head[(ny << 4) | nx];
                    while j_i != -1 {
                        let j = j_i as usize;
                        if j > i {
                            let dx = px[j] - px[i];
                            let dy = py[j] - py[i];
                            let rsum = rad[i] + rad[j];
                            let dist2 = dx * dx + dy * dy;
                            if dist2 < rsum * rsum && dist2 > 0 {
                                collisions += 1;
                                let mut dist = isqrt64(dist2);
                                if dist < 1 {
                                    dist = 1;
                                }
                                let half = (rsum - dist + 1) >> 1;
                                let sx = sdiv(dx * half, dist);
                                let sy = sdiv(dy * half, dist);
                                px[i] -= sx;
                                py[i] -= sy;
                                px[j] += sx;
                                py[j] += sy;
                                let vn = (vx[j] - vx[i]) * dx + (vy[j] - vy[i]) * dy;
                                if vn < 0 {
                                    let ix = sdiv(vn * dx, dist2);
                                    let iy = sdiv(vn * dy, dist2);
                                    vx[i] += ix;
                                    vy[i] += iy;
                                    vx[j] -= ix;
                                    vy[j] -= iy;
                                }
                            }
                        }
                        j_i = nxt_b[j];
                    }
                }
            }
        }
    }

    let mut ck: i64 = 0;
    for i in 0..N {
        let v = (px[i] + 100000) * 7
            + (py[i] + 100000) * 13
            + (vx[i] + 100000) * 17
            + (vy[i] + 100000);
        ck = (ck * 31 + (v % MOD_V)) % MOD_V;
    }

    println!("{}\n{}", collisions, ck);
}
