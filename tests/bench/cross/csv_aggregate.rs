fn main() {
    let prefixes = [
        "tokyo", "oslo", "lima", "cairo", "paris", "rome", "zurich", "seoul",
        "bergen", "kyoto", "milan", "vienna", "prague", "dublin", "lisbon", "athens",
    ];
    let mut st_bytes: Vec<i64> = Vec::with_capacity(1024);
    let mut st_off = [0usize; 64];
    let mut st_len = [0usize; 64];
    for i in 0..64usize {
        let p = prefixes[i & 15];
        st_off[i] = st_bytes.len();
        for b in p.bytes() {
            st_bytes.push(b as i64);
        }
        st_bytes.push(95);
        st_bytes.push(48 + ((i as i64) / 10));
        st_bytes.push(48 + ((i as i64) % 10));
        st_len[i] = st_bytes.len() - st_off[i];
    }

    let mut buf: Vec<i64> = Vec::with_capacity(1600000);
    let mut digs = [0i64; 16];
    let mut rng: i64 = 135792468;
    for _ in 0..100000 {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let si = ((rng >> 10) & 63) as usize;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let temp = (rng % 1999) - 999;
        let off = st_off[si];
        let ln = st_len[si];
        for k in 0..ln {
            buf.push(st_bytes[off + k]);
        }
        buf.push(59);
        let mut av = temp;
        if av < 0 {
            buf.push(45);
            av = -av;
        }
        let whole = av / 10;
        if whole == 0 {
            buf.push(48);
        } else {
            let mut w = whole;
            let mut dc = 0usize;
            while w > 0 {
                digs[dc] = 48 + (w % 10);
                dc += 1;
                w /= 10;
            }
            let mut di = dc;
            while di > 0 {
                di -= 1;
                buf.push(digs[di]);
            }
        }
        buf.push(46);
        buf.push(48 + (av % 10));
        buf.push(10);
    }

    let n = buf.len();
    let mut first_dot = 0usize;
    while first_dot < n && buf[first_dot] != 46 {
        first_dot += 1;
    }
    let orig_frac = buf[first_dot + 1] - 48;

    const CAP: usize = 256;
    const MASK: usize = 255;
    let mut k_start = [-1i64; CAP];
    let mut k_len = [0usize; CAP];
    let mut st_min = [0i64; CAP];
    let mut st_max = [0i64; CAP];
    let mut st_sum = [0i64; CAP];
    let mut st_cnt = [0i64; CAP];
    let mut occ = [0usize; CAP];

    let mut tot_rows: i64 = 0;
    let mut tot_ck: i64 = 0;
    for rd in 0i64..10 {
        buf[first_dot + 1] = 48 + ((orig_frac + rd) % 10);
        for slot in k_start.iter_mut() {
            *slot = -1;
        }
        let mut pos = 0usize;
        let mut rows: i64 = 0;
        while pos < n {
            let s_start = pos;
            let mut h: i64 = 0;
            while buf[pos] != 59 {
                h = (h * 131 + buf[pos]) & 2147483647;
                pos += 1;
            }
            let s_len = pos - s_start;
            pos += 1;
            let mut neg = false;
            if buf[pos] == 45 {
                neg = true;
                pos += 1;
            }
            let mut v: i64 = 0;
            while buf[pos] != 46 {
                v = v * 10 + (buf[pos] - 48);
                pos += 1;
            }
            pos += 1;
            v = v * 10 + (buf[pos] - 48);
            pos += 1;
            if neg {
                v = -v;
            }
            if pos < n && buf[pos] == 10 {
                pos += 1;
            }
            rows += 1;

            let mut slot = (h as usize) & MASK;
            loop {
                let ks = k_start[slot];
                if ks == -1 {
                    k_start[slot] = s_start as i64;
                    k_len[slot] = s_len;
                    st_min[slot] = v;
                    st_max[slot] = v;
                    st_sum[slot] = v;
                    st_cnt[slot] = 1;
                    break;
                }
                if k_len[slot] == s_len {
                    let ksu = ks as usize;
                    let mut eq = true;
                    for ci in 0..s_len {
                        if buf[ksu + ci] != buf[s_start + ci] {
                            eq = false;
                            break;
                        }
                    }
                    if eq {
                        if v < st_min[slot] {
                            st_min[slot] = v;
                        }
                        if v > st_max[slot] {
                            st_max[slot] = v;
                        }
                        st_sum[slot] += v;
                        st_cnt[slot] += 1;
                        break;
                    }
                }
                slot = (slot + 1) & MASK;
            }
        }

        let mut occ_len = 0usize;
        for i in 0..CAP {
            if k_start[i] != -1 {
                occ[occ_len] = i;
                occ_len += 1;
            }
        }
        for i in 1..occ_len {
            let key_slot = occ[i];
            let mut j = i;
            while j > 0 {
                let a = occ[j - 1];
                let la = k_len[a];
                let lb = k_len[key_slot];
                let ml = if la < lb { la } else { lb };
                let ka = k_start[a] as usize;
                let kb = k_start[key_slot] as usize;
                let mut cmp = 0i64;
                for t in 0..ml {
                    let ba = buf[ka + t];
                    let bb = buf[kb + t];
                    if ba != bb {
                        cmp = if ba < bb { -1 } else { 1 };
                        break;
                    }
                }
                if cmp == 0 {
                    if la < lb {
                        cmp = -1;
                    } else if la > lb {
                        cmp = 1;
                    }
                }
                if cmp > 0 {
                    occ[j] = occ[j - 1];
                    j -= 1;
                } else {
                    break;
                }
            }
            occ[j] = key_slot;
        }

        let mut ck: i64 = 0;
        for i in 0..occ_len {
            let sl = occ[i];
            let mut s_mod = st_sum[sl] % 1000000007;
            if s_mod < 0 {
                s_mod += 1000000007;
            }
            let term = (((i as i64) + 1) * 7
                + (st_min[sl] + 1000) * 13
                + (st_max[sl] + 1000) * 17
                + st_cnt[sl] * 19
                + s_mod)
                % 1000000007;
            ck = (ck * 1000003 + term) % 1000000007;
        }
        tot_rows += rows;
        tot_ck = (tot_ck * 31 + ck) % 1000000007;
    }
    println!("{}\n{}", tot_rows, tot_ck);
}
