const MOD_V: i64 = 1000000007;

fn less_rec(k1: i64, s1: i64, k2: i64, s2: i64) -> bool {
    if k1 != k2 {
        return k1 < k2;
    }
    s1 > s2
}

fn swap_run(rk: &mut [i64], rs: &mut [i64], rv: &mut [i64], rt: &mut [i64], a: usize, b: usize) {
    rk.swap(a, b);
    rs.swap(a, b);
    rv.swap(a, b);
    rt.swap(a, b);
}

fn sift_max_run(
    rk: &mut [i64],
    rs: &mut [i64],
    rv: &mut [i64],
    rt: &mut [i64],
    start: usize,
    n: usize,
) {
    let mut i = start;
    loop {
        let l = i * 2 + 1;
        if l >= n {
            break;
        }
        let mut best = l;
        let r = l + 1;
        if r < n && less_rec(rk[best], rs[best], rk[r], rs[r]) {
            best = r;
        }
        if less_rec(rk[i], rs[i], rk[best], rs[best]) {
            swap_run(rk, rs, rv, rt, i, best);
            i = best;
        } else {
            break;
        }
    }
}

fn heapsort_run(rk: &mut [i64], rs: &mut [i64], rv: &mut [i64], rt: &mut [i64], n: usize) {
    let mut start = n / 2;
    while start > 0 {
        start -= 1;
        sift_max_run(rk, rs, rv, rt, start, n);
    }
    let mut end = n;
    while end > 1 {
        end -= 1;
        swap_run(rk, rs, rv, rt, 0, end);
        sift_max_run(rk, rs, rv, rt, 0, end);
    }
}

fn heap_less(all_k: &[i64], all_s: &[i64], run_pos: &[usize], ra: usize, rb: usize) -> bool {
    let pa = run_pos[ra];
    let pb = run_pos[rb];
    less_rec(all_k[pa], all_s[pa], all_k[pb], all_s[pb])
}

fn sift_min_merge(
    heap: &mut [usize],
    hsz: usize,
    all_k: &[i64],
    all_s: &[i64],
    run_pos: &[usize],
) {
    let mut i = 0usize;
    loop {
        let l = i * 2 + 1;
        if l >= hsz {
            break;
        }
        let mut best = l;
        let rr = l + 1;
        if rr < hsz && heap_less(all_k, all_s, run_pos, heap[rr], heap[best]) {
            best = rr;
        }
        if heap_less(all_k, all_s, run_pos, heap[best], heap[i]) {
            heap.swap(i, best);
            i = best;
        } else {
            break;
        }
    }
}

fn main() {
    let mut rng: i64 = 555123456;
    let mut global_seq: i64 = 1;
    let mut l1_k: Vec<i64> = Vec::new();
    let mut l1_v: Vec<i64> = Vec::new();
    let mut hits: i64 = 0;
    let mut ck: i64 = 0;

    let mut rk = vec![0i64; 12000];
    let mut rs = vec![0i64; 12000];
    let mut rv = vec![0i64; 12000];
    let mut rt = vec![0i64; 12000];

    for _cyc in 0..4 {
        let mut all_k: Vec<i64> = Vec::with_capacity(120000);
        let mut all_s: Vec<i64> = Vec::with_capacity(120000);
        let mut all_v: Vec<i64> = Vec::with_capacity(120000);
        let mut all_t: Vec<i64> = Vec::with_capacity(120000);
        let mut run_pos: Vec<usize> = Vec::with_capacity(9);
        let mut run_end: Vec<usize> = Vec::with_capacity(9);

        for _rn in 0..8 {
            for j in 0..12000 {
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let k = rng % 40000;
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let tomb = if (rng % 10) == 0 { 1 } else { 0 };
                let mut val = 0;
                if tomb == 0 {
                    rng = (rng * 1103515245 + 12345) & 2147483647;
                    val = 1 + (rng % 100000);
                }
                rk[j] = k;
                rs[j] = global_seq;
                rv[j] = val;
                rt[j] = tomb;
                global_seq += 1;
            }
            heapsort_run(&mut rk, &mut rs, &mut rv, &mut rt, 12000);
            let st = all_k.len();
            let mut prev_k: i64 = -1;
            for j in 0..12000 {
                if rk[j] != prev_k {
                    all_k.push(rk[j]);
                    all_s.push(rs[j]);
                    all_v.push(rv[j]);
                    all_t.push(rt[j]);
                    prev_k = rk[j];
                }
            }
            run_pos.push(st);
            run_end.push(all_k.len());
        }

        if !l1_k.is_empty() {
            let st = all_k.len();
            for j in 0..l1_k.len() {
                all_k.push(l1_k[j]);
                all_s.push(0);
                all_v.push(l1_v[j]);
                all_t.push(0);
            }
            run_pos.push(st);
            run_end.push(all_k.len());
        }

        let mut heap: Vec<usize> = Vec::with_capacity(run_pos.len());
        for r in 0..run_pos.len() {
            if run_pos[r] < run_end[r] {
                heap.push(r);
                let mut hi = heap.len() - 1;
                while hi > 0 {
                    let p = (hi - 1) >> 1;
                    if heap_less(&all_k, &all_s, &run_pos, heap[hi], heap[p]) {
                        heap.swap(hi, p);
                        hi = p;
                    } else {
                        break;
                    }
                }
            }
        }

        let mut new_k: Vec<i64> = Vec::with_capacity(40000);
        let mut new_v: Vec<i64> = Vec::with_capacity(40000);
        let mut last_k: i64 = -1;
        let mut hsz = heap.len();
        while hsz > 0 {
            let top_r = heap[0];
            let pos = run_pos[top_r];
            let k = all_k[pos];
            let v = all_v[pos];
            let t = all_t[pos];
            run_pos[top_r] = pos + 1;
            if run_pos[top_r] < run_end[top_r] {
                sift_min_merge(&mut heap, hsz, &all_k, &all_s, &run_pos);
            } else {
                hsz -= 1;
                if hsz > 0 {
                    heap[0] = heap[hsz];
                    sift_min_merge(&mut heap, hsz, &all_k, &all_s, &run_pos);
                }
            }
            if k != last_k {
                last_k = k;
                if t == 0 {
                    new_k.push(k);
                    new_v.push(v);
                }
            }
        }

        l1_k = new_k;
        l1_v = new_v;
        let n_l1 = l1_k.len();
        ck = (ck * 37 + n_l1 as i64) % MOD_V;

        for _q in 0..60000 {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let qk = rng % 40000;
            let mut lo = 0usize;
            let mut hi = n_l1;
            while lo < hi {
                let mid = (lo + hi) >> 1;
                if l1_k[mid] < qk {
                    lo = mid + 1;
                } else {
                    hi = mid;
                }
            }
            if lo < n_l1 && l1_k[lo] == qk {
                hits += 1;
                ck = (ck * 31 + l1_v[lo]) % MOD_V;
            }
        }
    }

    println!("{}\n{}", hits, ck);
}
