const MOD_V: i64 = 1000000007;

fn enc_cp(out: &mut Vec<i64>, cp: i64) {
    if cp < 128 {
        out.push(cp);
    } else if cp < 2048 {
        out.push(192 | (cp >> 6));
        out.push(128 | (cp & 63));
    } else if cp < 65536 {
        out.push(224 | (cp >> 12));
        out.push(128 | ((cp >> 6) & 63));
        out.push(128 | (cp & 63));
    } else {
        out.push(240 | (cp >> 18));
        out.push(128 | ((cp >> 12) & 63));
        out.push(128 | ((cp >> 6) & 63));
        out.push(128 | (cp & 63));
    }
}

fn main() {
    let mut rng: i64 = 246801357;
    let mut src: Vec<i64> = Vec::with_capacity(65600);

    while src.len() < 65520 {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let r = rng % 100;
        if r < 38 {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let k = rng % 62;
            let cp = if k < 26 {
                65 + k
            } else if k < 52 {
                97 + (k - 26)
            } else {
                48 + (k - 52)
            };
            enc_cp(&mut src, cp);
        } else if r < 52 {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let cp = match rng % 6 {
                0 => 32,
                1 => 9,
                2 => 10,
                3 => 13,
                4 => 160,
                _ => 12288,
            };
            enc_cp(&mut src, cp);
        } else if r < 64 {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let g = rng % 3;
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let cp = if g == 0 {
                192 + (rng % 62)
            } else if g == 1 {
                913 + (rng % 40)
            } else {
                1040 + (rng % 64)
            };
            enc_cp(&mut src, cp);
        } else if r < 78 {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let cp = if (rng & 3) == 0 {
                rng = (rng * 1103515245 + 12345) & 2147483647;
                match rng & 3 {
                    0 => 8216,
                    1 => 8217,
                    2 => 8220,
                    _ => 8221,
                }
            } else {
                rng = (rng * 1103515245 + 12345) & 2147483647;
                65281 + (rng % 94)
            };
            enc_cp(&mut src, cp);
        } else if r < 90 {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            enc_cp(&mut src, 19968 + (rng % 512));
        } else if r < 97 {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            enc_cp(&mut src, 128512 + (rng % 64));
        } else {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let inv = rng % 4;
            if inv == 0 {
                rng = (rng * 1103515245 + 12345) & 2147483647;
                src.push(128 + (rng % 64));
            } else if inv == 1 {
                src.push(192);
                src.push(175);
            } else if inv == 2 {
                src.push(237);
                src.push(160);
                src.push(128);
            } else {
                src.push(244);
                src.push(144);
                src.push(128);
                src.push(128);
            }
        }
    }

    let n = src.len();
    let mut out_buf = vec![0i64; n * 3];
    let mut total_out: i64 = 0;
    let mut ck: i64 = 0;

    for _rnd in 0..40 {
        let mut i = 0usize;
        let mut olen = 0usize;
        let mut in_ws = true;
        while i < n {
            let b0 = src[i];
            let mut cp: i64 = 65533;
            let mut adv = 1usize;
            if b0 < 128 {
                cp = b0;
                adv = 1;
            } else if b0 >= 194 && b0 <= 223 {
                if i + 1 < n && (src[i + 1] & 192) == 128 {
                    cp = ((b0 & 31) << 6) | (src[i + 1] & 63);
                    adv = 2;
                }
            } else if b0 >= 224 && b0 <= 239 {
                if i + 2 < n && (src[i + 1] & 192) == 128 && (src[i + 2] & 192) == 128 {
                    let c = ((b0 & 15) << 12) | ((src[i + 1] & 63) << 6) | (src[i + 2] & 63);
                    if c >= 2048 && (c < 55296 || c > 57343) {
                        cp = c;
                        adv = 3;
                    }
                }
            } else if b0 >= 240 && b0 <= 244 {
                if i + 3 < n
                    && (src[i + 1] & 192) == 128
                    && (src[i + 2] & 192) == 128
                    && (src[i + 3] & 192) == 128
                {
                    let c = ((b0 & 7) << 18)
                        | ((src[i + 1] & 63) << 12)
                        | ((src[i + 2] & 63) << 6)
                        | (src[i + 3] & 63);
                    if c >= 65536 && c <= 1114111 {
                        cp = c;
                        adv = 4;
                    }
                }
            }
            i += adv;

            if cp == 32 || cp == 9 || cp == 10 || cp == 13 || cp == 160 || cp == 12288 {
                if !in_ws {
                    out_buf[olen] = 32;
                    olen += 1;
                    in_ws = true;
                }
                continue;
            }
            in_ws = false;
            if cp >= 65281 && cp <= 65374 {
                cp -= 65248;
            }
            if cp >= 65 && cp <= 90 {
                cp += 32;
            } else if (cp >= 192 && cp <= 214) || (cp >= 216 && cp <= 222) {
                cp += 32;
            } else if (cp >= 913 && cp <= 929) || (cp >= 931 && cp <= 939) {
                cp += 32;
            } else if cp >= 1040 && cp <= 1071 {
                cp += 32;
            } else if cp == 8216 || cp == 8217 {
                cp = 39;
            } else if cp == 8220 || cp == 8221 {
                cp = 34;
            }

            if cp < 128 {
                out_buf[olen] = cp;
                olen += 1;
            } else if cp < 2048 {
                out_buf[olen] = 192 | (cp >> 6);
                out_buf[olen + 1] = 128 | (cp & 63);
                olen += 2;
            } else if cp < 65536 {
                out_buf[olen] = 224 | (cp >> 12);
                out_buf[olen + 1] = 128 | ((cp >> 6) & 63);
                out_buf[olen + 2] = 128 | (cp & 63);
                olen += 3;
            } else {
                out_buf[olen] = 240 | (cp >> 18);
                out_buf[olen + 1] = 128 | ((cp >> 12) & 63);
                out_buf[olen + 2] = 128 | ((cp >> 6) & 63);
                out_buf[olen + 3] = 128 | (cp & 63);
                olen += 4;
            }
        }

        let mut h = olen as i64;
        for j in 0..olen {
            h = (h * 131 + out_buf[j]) % MOD_V;
        }
        total_out += olen as i64;
        ck = (ck * 31 + h) % MOD_V;
    }

    println!("{}\n{}", total_out, ck);
}
