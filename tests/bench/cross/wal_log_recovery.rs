const MOD_V: i64 = 1000000007;

fn crc32_slice(crc_tbl: &[i64], buf: &[i64], start: usize, length: usize) -> i64 {
    const MASK32: i64 = 4294967295;
    let mut c = MASK32;
    let end = start + length;
    for i in start..end {
        let idx = ((c ^ buf[i]) & 255) as usize;
        c = crc_tbl[idx] ^ (c >> 8);
    }
    c ^ MASK32
}

fn kv_put(kv_key: &mut [i64], kv_val: &mut [i64], k: i64, v: i64) {
    const KV_MASK: i64 = 8191;
    let mut slot = (((k * 2654435761) >> 16) & KV_MASK) as usize;
    let mut first_tomb: i64 = -1;
    loop {
        let cur = kv_key[slot];
        if cur == k {
            kv_val[slot] = v;
            return;
        }
        if cur == -1 {
            let dst = if first_tomb != -1 { first_tomb as usize } else { slot };
            kv_key[dst] = k;
            kv_val[dst] = v;
            return;
        }
        if cur == -2 && first_tomb == -1 {
            first_tomb = slot as i64;
        }
        slot = (slot + 1) & (KV_MASK as usize);
    }
}

fn kv_del(kv_key: &mut [i64], kv_val: &mut [i64], k: i64) {
    const KV_MASK: i64 = 8191;
    let mut slot = (((k * 2654435761) >> 16) & KV_MASK) as usize;
    loop {
        let cur = kv_key[slot];
        if cur == -1 {
            return;
        }
        if cur == k {
            kv_key[slot] = -2;
            kv_val[slot] = 0;
            return;
        }
        slot = (slot + 1) & (KV_MASK as usize);
    }
}

fn kv_get(kv_key: &[i64], kv_val: &[i64], k: i64) -> i64 {
    const KV_MASK: i64 = 8191;
    let mut slot = (((k * 2654435761) >> 16) & KV_MASK) as usize;
    loop {
        let cur = kv_key[slot];
        if cur == -1 {
            return -1;
        }
        if cur == k {
            return kv_val[slot];
        }
        slot = (slot + 1) & (KV_MASK as usize);
    }
}

fn main() {
    const POLY: i64 = 3988292384;
    let mut crc_tbl = [0i64; 256];
    for i in 0..256 {
        let mut c = i as i64;
        for _ in 0..8 {
            if (c & 1) != 0 {
                c = POLY ^ (c >> 1);
            } else {
                c >>= 1;
            }
        }
        crc_tbl[i] = c;
    }

    const KV_CAP: usize = 8192;
    let mut kv_key = vec![-1i64; KV_CAP];
    let mut kv_val = vec![0i64; KV_CAP];
    let mut buf = vec![0i64; 180000];

    let mut rng: i64 = 999888777;
    let mut lsn: i64 = 1;
    let mut replayed: i64 = 0;
    let mut ck: i64 = 0;

    for seg in 0i64..40 {
        let mut blen = 0usize;
        for _rec in 0..3000 {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let op = if (rng % 6) == 0 { 2 } else { 1 };
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let key = rng % 4096;
            let mut vlen: i64 = 0;
            if op == 1 {
                rng = (rng * 1103515245 + 12345) & 2147483647;
                vlen = 8 + (rng % 32);
            }
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let seed = (rng >> 4) & 255;

            let rec_start = blen;
            buf[blen] = 87;
            buf[blen + 1] = 76;
            buf[blen + 2] = op;
            buf[blen + 3] = (lsn ^ key) & 255;
            buf[blen + 4] = lsn & 255;
            buf[blen + 5] = (lsn >> 8) & 255;
            buf[blen + 6] = (lsn >> 16) & 255;
            buf[blen + 7] = (lsn >> 24) & 255;
            buf[blen + 8] = key & 255;
            buf[blen + 9] = (key >> 8) & 255;
            buf[blen + 10] = (key >> 16) & 255;
            buf[blen + 11] = (key >> 24) & 255;
            buf[blen + 12] = vlen & 255;
            buf[blen + 13] = (vlen >> 8) & 255;
            blen += 14;
            let vl = vlen as usize;
            for j in 0..vl {
                buf[blen] = (seed + (j as i64) * 13 + lsn) & 255;
                blen += 1;
            }
            let crc = crc32_slice(&crc_tbl, &buf, rec_start, 14 + vl);
            buf[blen] = crc & 255;
            buf[blen + 1] = (crc >> 8) & 255;
            buf[blen + 2] = (crc >> 16) & 255;
            buf[blen + 3] = (crc >> 24) & 255;
            blen += 4;
            lsn += 1;
        }

        if (seg % 4) == 3 {
            blen -= 7;
        } else if (seg % 5) == 4 {
            buf[blen - 2] ^= 1;
        }

        let mut pos = 0usize;
        let mut seg_rep: i64 = 0;
        let mut early: i64 = 0;
        while pos < blen {
            if pos + 18 > blen {
                early = 1;
                break;
            }
            if buf[pos] != 87 || buf[pos + 1] != 76 {
                early = 1;
                break;
            }
            let op = buf[pos + 2];
            if op != 1 && op != 2 {
                early = 1;
                break;
            }
            let vlen = (buf[pos + 12] | (buf[pos + 13] << 8)) as usize;
            if pos + 18 + vlen > blen {
                early = 1;
                break;
            }
            let stored = buf[pos + 14 + vlen]
                | (buf[pos + 15 + vlen] << 8)
                | (buf[pos + 16 + vlen] << 16)
                | (buf[pos + 17 + vlen] << 24);
            let calc = crc32_slice(&crc_tbl, &buf, pos, 14 + vlen);
            if calc != stored {
                early = 1;
                break;
            }
            let key = buf[pos + 8]
                | (buf[pos + 9] << 8)
                | (buf[pos + 10] << 16)
                | (buf[pos + 11] << 24);
            if op == 1 {
                let mut vh: i64 = 0;
                for j in 0..vlen {
                    vh = (vh * 131 + buf[pos + 14 + j]) % MOD_V;
                }
                kv_put(&mut kv_key, &mut kv_val, key, vh);
            } else {
                kv_del(&mut kv_key, &mut kv_val, key);
            }
            seg_rep += 1;
            pos += 18 + vlen;
        }
        replayed += seg_rep;
        ck = (ck * 37 + seg * 1009 + seg_rep * 17 + early) % MOD_V;
    }

    for k in 0i64..4096 {
        let v = kv_get(&kv_key, &kv_val, k);
        if v >= 0 {
            ck = (ck * 31 + k * 97 + v) % MOD_V;
        }
    }

    println!("{}\n{}", replayed, ck);
}
