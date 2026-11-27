fn main() {
    let mut cx = [0.0f64; 16];
    let mut cy = [0.0f64; 16];
    let mut cz = [0.0f64; 16];
    let mut cr = [0.0f64; 16];
    let mut sr = [0.0f64; 16];
    let mut sg = [0.0f64; 16];
    let mut sb = [0.0f64; 16];
    let mut refl = [0.0f64; 16];

    cx[0] = 0.0;
    cy[0] = -1001.5;
    cz[0] = -6.0;
    cr[0] = 1000.0;
    sr[0] = 0.45;
    sg[0] = 0.48;
    sb[0] = 0.52;
    refl[0] = 0.25;

    let mut rng: i64 = 44556677;
    for i in 1..16 {
        let row = (i - 1) / 5;
        let col = (i - 1) % 5;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        cx[i] = -3.2 + (col as f64) * 1.6 + (((rng % 41) - 20) as f64) / 128.0;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        cy[i] = -0.7 + (row as f64) * 1.1 + (((rng % 33) - 16) as f64) / 128.0;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        cz[i] = -4.2 - (row as f64) * 1.8 - ((rng % 33) as f64) / 64.0;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        cr[i] = 0.45 + ((rng % 17) as f64) / 64.0;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        sr[i] = 0.25 + ((rng % 48) as f64) / 64.0;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        sg[i] = 0.25 + ((rng % 48) as f64) / 64.0;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        sb[i] = 0.25 + ((rng % 48) as f64) / 64.0;
        refl[i] = 0.2 + ((i % 4) as f64) * 0.15;
    }

    const LX: f64 = 0.5773502691896258;
    const LY: f64 = 0.5773502691896258;
    const LZ: f64 = 0.5773502691896258;
    const W: usize = 320;
    const H: usize = 240;
    let mut hit_count: i64 = 0;
    let mut total_lum: f64 = 0.0;

    for py in 0..H {
        let v = (0.5 - ((py as f64) + 0.5) / 240.0) * 1.5;
        for px in 0..W {
            let u = (((px as f64) + 0.5) / 320.0 - 0.5) * 2.0;
            let inv_l = 1.0 / (u * u + v * v + 1.0).sqrt();
            let mut ox = 0.0;
            let mut oy = 0.2;
            let mut oz = 0.0;
            let mut dx = u * inv_l;
            let mut dy = v * inv_l;
            let mut dz = -1.0 * inv_l;
            let mut att = 1.0;
            let mut pr = 0.0;
            let mut pg = 0.0;
            let mut pb = 0.0;

            for _depth in 0..3 {
                let mut best_t = 1.0e18;
                let mut best_i: i64 = -1;
                for i in 0..16 {
                    let ocx = ox - cx[i];
                    let ocy = oy - cy[i];
                    let ocz = oz - cz[i];
                    let b = ocx * dx + ocy * dy + ocz * dz;
                    let c = ocx * ocx + ocy * ocy + ocz * ocz - cr[i] * cr[i];
                    let disc = b * b - c;
                    if disc > 0.0 {
                        let t = -b - disc.sqrt();
                        if t > 0.0005 && t < best_t {
                            best_t = t;
                            best_i = i as i64;
                        }
                    }
                }
                if best_i == -1 {
                    let sky = 0.5 * (dy + 1.0);
                    pr += att * (0.2 + 0.4 * sky);
                    pg += att * (0.3 + 0.4 * sky);
                    pb += att * (0.5 + 0.4 * sky);
                    break;
                }
                hit_count += 1;
                let bi = best_i as usize;
                let hx = ox + dx * best_t;
                let hy = oy + dy * best_t;
                let hz = oz + dz * best_t;
                let inv_r = 1.0 / cr[bi];
                let nx = (hx - cx[bi]) * inv_r;
                let ny = (hy - cy[bi]) * inv_r;
                let nz = (hz - cz[bi]) * inv_r;

                let sox = hx + nx * 0.002;
                let soy = hy + ny * 0.002;
                let soz = hz + nz * 0.002;
                let mut in_shadow = false;
                for j in 0..16 {
                    let ocx = sox - cx[j];
                    let ocy = soy - cy[j];
                    let ocz = soz - cz[j];
                    let b = ocx * LX + ocy * LY + ocz * LZ;
                    let c = ocx * ocx + ocy * ocy + ocz * ocz - cr[j] * cr[j];
                    let disc = b * b - c;
                    if disc > 0.0 {
                        let st = -b - disc.sqrt();
                        if st > 0.0005 {
                            in_shadow = true;
                            break;
                        }
                    }
                }

                let mut diff = 0.0;
                let mut spec = 0.0;
                if !in_shadow {
                    let ndotl = nx * LX + ny * LY + nz * LZ;
                    if ndotl > 0.0 {
                        diff = ndotl;
                        let hx2 = LX - dx;
                        let hy2 = LY - dy;
                        let hz2 = LZ - dz;
                        let hinv = 1.0 / (hx2 * hx2 + hy2 * hy2 + hz2 * hz2).sqrt();
                        let ndoth = (nx * hx2 + ny * hy2 + nz * hz2) * hinv;
                        if ndoth > 0.0 {
                            let s2 = ndoth * ndoth;
                            let s4 = s2 * s2;
                            spec = s4 * s4 * 0.5;
                        }
                    }
                }
                let shade = 0.1 + 0.75 * diff;
                let kr = refl[bi];
                pr += att * (1.0 - kr) * (sr[bi] * shade + spec);
                pg += att * (1.0 - kr) * (sg[bi] * shade + spec);
                pb += att * (1.0 - kr) * (sb[bi] * shade + spec);
                att *= kr;
                if att < 0.02 {
                    break;
                }
                let dot2 = 2.0 * (dx * nx + dy * ny + dz * nz);
                dx -= dot2 * nx;
                dy -= dot2 * ny;
                dz -= dot2 * nz;
                ox = sox;
                oy = soy;
                oz = soz;
            }
            total_lum += pr + pg + pb;
        }
    }

    println!("{}\n{}", hit_count, (total_lum * 10.0 + 0.5).floor() as i64);
}
