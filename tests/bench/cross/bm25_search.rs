const MOD_V: i64 = 1000000007;

fn ilog2_x1000(x: i64, lut: &[i64; 16]) -> i64 {
    let mut b: i64 = 0;
    let mut t = x;
    while t >= 2 {
        t >>= 1;
        b += 1;
    }
    let frac = (((x - (1i64 << b)) << 4) >> b) as usize;
    b * 1000 + lut[frac]
}

fn main() {
    const N_DOCS: usize = 6000;
    const VOCAB: usize = 2048;
    let mut rng: i64 = 777654321;
    let lut: [i64; 16] = [0, 87, 170, 248, 322, 392, 459, 524, 585, 644, 700, 755, 807, 858, 907, 954];

    let mut doc_len = vec![0i64; N_DOCS];
    let mut scores = vec![0i64; N_DOCS];
    let mut stamp = vec![0i64; N_DOCS];
    let mut touched = vec![0usize; N_DOCS];

    let mut df = vec![0i64; VOCAB];
    let mut post_off = vec![0usize; VOCAB + 1];
    let mut cur = vec![0usize; VOCAB];
    let mut idf = vec![0i64; VOCAB];

    let mut raw_d: Vec<usize> = Vec::with_capacity(N_DOCS * 40);
    let mut raw_t: Vec<usize> = Vec::with_capacity(N_DOCS * 40);
    let mut raw_f: Vec<i64> = Vec::with_capacity(N_DOCS * 40);
    let mut tmp = [0usize; 64];

    let mut total_len: i64 = 0;
    for d in 0..N_DOCS {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let dl = (24 + (rng % 32)) as usize;
        doc_len[d] = dl as i64;
        total_len += dl as i64;
        for j in 0..dl {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let term = if (rng % 3) == 0 {
                rng = (rng * 1103515245 + 12345) & 2147483647;
                (rng % 64) as usize
            } else {
                rng = (rng * 1103515245 + 12345) & 2147483647;
                64 + (rng % (VOCAB as i64 - 64)) as usize
            };
            tmp[j] = term;
        }
        for j in 1..dl {
            let key = tmp[j];
            let mut p = j;
            while p > 0 && tmp[p - 1] > key {
                tmp[p] = tmp[p - 1];
                p -= 1;
            }
            tmp[p] = key;
        }
        let mut j = 0usize;
        while j < dl {
            let term = tmp[j];
            let mut cnt = 1usize;
            while j + cnt < dl && tmp[j + cnt] == term {
                cnt += 1;
            }
            df[term] += 1;
            raw_d.push(d);
            raw_t.push(term);
            raw_f.push(cnt as i64);
            j += cnt;
        }
    }

    for t in 0..VOCAB {
        post_off[t + 1] = post_off[t] + df[t] as usize;
        cur[t] = post_off[t];
    }
    let total_p = post_off[VOCAB];
    let mut post_doc = vec![0usize; total_p];
    let mut post_tf = vec![0i64; total_p];
    for i in 0..raw_d.len() {
        let term = raw_t[i];
        let idx = cur[term];
        post_doc[idx] = raw_d[i];
        post_tf[idx] = raw_f[i];
        cur[term] = idx + 1;
    }

    for t in 0..VOCAB {
        if df[t] > 0 {
            let ratio_x1024 = (((N_DOCS as i64 - df[t]) * 2 + 1) * 1024) / (df[t] * 2 + 1) + 1024;
            idf[t] = ilog2_x1000(ratio_x1024, &lut) - 10000;
        }
    }

    let avgdl_x100 = (total_len * 100) / (N_DOCS as i64);
    let mut dl_norm = vec![0i64; N_DOCS];
    for d in 0..N_DOCS {
        dl_norm[d] = 250 + (750 * doc_len[d] * 100) / avgdl_x100;
    }

    let mut qterms = [0usize; 5];
    let mut top_d = [0usize; 10];
    let mut top_s = [0i64; 10];
    let mut total_hits: i64 = 0;
    let mut ck: i64 = 0;

    for q in 1i64..=2000 {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let qn = (3 + (rng % 3)) as usize;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        qterms[0] = (rng % 64) as usize;
        for j in 1..qn {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            qterms[j] = 64 + (rng % (VOCAB as i64 - 64)) as usize;
        }
        let mut t_cnt = 0usize;
        for j in 0..qn {
            let term = qterms[j];
            let it = idf[term];
            if it > 0 {
                let pend = post_off[term + 1];
                for p in post_off[term]..pend {
                    let doc_i = post_doc[p];
                    let tf = post_tf[p];
                    let sc = (it * tf * 2200) / (tf * 1000 + (12 * dl_norm[doc_i]) / 10);
                    if stamp[doc_i] != q {
                        stamp[doc_i] = q;
                        scores[doc_i] = sc;
                        touched[t_cnt] = doc_i;
                        t_cnt += 1;
                    } else {
                        scores[doc_i] += sc;
                    }
                }
            }
        }
        let mut k_found = 0usize;
        for i in 0..t_cnt {
            let doc_i = touched[i];
            let s = scores[doc_i];
            if k_found < 10 || s > top_s[9] || (s == top_s[9] && doc_i < top_d[9]) {
                let mut pos = if k_found < 10 {
                    let cur_k = k_found;
                    k_found += 1;
                    cur_k
                } else {
                    9
                };
                while pos > 0 && (s > top_s[pos - 1] || (s == top_s[pos - 1] && doc_i < top_d[pos - 1])) {
                    top_s[pos] = top_s[pos - 1];
                    top_d[pos] = top_d[pos - 1];
                    pos -= 1;
                }
                top_s[pos] = s;
                top_d[pos] = doc_i;
            }
        }
        total_hits += k_found as i64;
        for r in 0..k_found {
            ck = (ck * 31 + (top_d[r] as i64) * 10007 + top_s[r]) % MOD_V;
        }
    }

    println!("{}\n{}", total_hits, ck);
}
