#[inline(always)]
fn lcg(seed: i64) -> i64 {
    (seed * 1103515245 + 12345) & 2147483647
}

fn main() {
    let n = 200_000usize;
    let q = 200_000usize;
    let mut st = Vec::with_capacity(n);
    let mut en = Vec::with_capacity(n);
    let mut max_en = vec![0i64; n];

    let mut seed: i64 = 123456789;
    let mut cur_st: i64 = 0;
    for _ in 0..n {
        seed = lcg(seed);
        cur_st += seed % 100;
        seed = lcg(seed);
        let ln = 1 + (seed % 5000);
        st.push(cur_st);
        en.push(cur_st + ln);
    }
    let max_coord = cur_st + 1;

    let mut qst = Vec::with_capacity(q);
    let mut qen = Vec::with_capacity(q);
    for _ in 0..q {
        seed = lcg(seed);
        let qs = seed % max_coord;
        seed = lcg(seed);
        let ln = 1 + (seed % 5000);
        qst.push(qs);
        qen.push(qs + ln);
    }

    let mut i = 0usize;
    while i < n {
        max_en[i] = en[i];
        i += 2;
    }
    let mut k = 1usize;
    while (1usize << k) <= n {
        let x = 1usize << (k - 1);
        let i0 = (x << 1) - 1;
        let step = x << 2;
        let mut idx = i0;
        while idx < n {
            let el = max_en[idx - x];
            let er = if idx + x < n {
                max_en[idx + x]
            } else {
                let mut m = en[idx];
                let lim = (idx + (x << 1)).min(n);
                for j in (idx + 1)..lim {
                    if en[j] > m {
                        m = en[j];
                    }
                }
                m
            };
            let mut e = en[idx];
            if el > e {
                e = el;
            }
            if er > e {
                e = er;
            }
            max_en[idx] = e;
            idx += step;
        }
        k += 1;
    }
    let max_k = k - 1;

    let mut sk = [0usize; 64];
    let mut sx = [0usize; 64];
    let mut sw = [0u8; 64];
    let mut hits: i64 = 0;
    let mut cov_sum: i64 = 0;
    let root_x = (1usize << max_k) - 1;

    for qi in 0..q {
        let qs = qst[qi];
        let qe = qen[qi];
        sk[0] = max_k;
        sx[0] = root_x;
        sw[0] = 0;
        let mut sp = 1usize;
        while sp > 0 {
            sp -= 1;
            let kk = sk[sp];
            let x = sx[sp];
            let w = sw[sp];
            if kk <= 3 {
                let i0 = (x >> kk) << kk;
                let i1 = (i0 + (1usize << (kk + 1)) - 1).min(n);
                let mut ii = i0;
                while ii < i1 && st[ii] < qe {
                    if qs < en[ii] {
                        hits += 1;
                        let os = if qs > st[ii] { qs } else { st[ii] };
                        let oe = if qe < en[ii] { qe } else { en[ii] };
                        cov_sum += oe - os;
                    }
                    ii += 1;
                }
            } else if w == 0 {
                let y = x - (1usize << (kk - 1));
                sk[sp] = kk;
                sx[sp] = x;
                sw[sp] = 1;
                sp += 1;
                if y >= n || max_en[y] > qs {
                    sk[sp] = kk - 1;
                    sx[sp] = y;
                    sw[sp] = 0;
                    sp += 1;
                }
            } else if x < n && st[x] < qe {
                if qs < en[x] {
                    hits += 1;
                    let os = if qs > st[x] { qs } else { st[x] };
                    let oe = if qe < en[x] { qe } else { en[x] };
                    cov_sum += oe - os;
                }
                sk[sp] = kk - 1;
                sx[sp] = x + (1usize << (kk - 1));
                sw[sp] = 0;
                sp += 1;
            }
        }
    }
    println!("{}\n{}", hits, cov_sum);
}
