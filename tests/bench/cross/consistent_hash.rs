const MOD_V: i64 = 1000000007;

fn mix32(x: i64) -> i64 {
    const MASK: i64 = 4294967295;
    const MUL: i64 = 73244475;
    let mut h = x & MASK;
    h ^= h >> 16;
    h = (h * MUL) & MASK;
    h ^= h >> 16;
    h = (h * MUL) & MASK;
    h ^= h >> 16;
    h
}

fn sift_max_ring(rt: &mut [i64], rn: &mut [i64], start: usize, n: usize) {
    let mut i = start;
    loop {
        let l = i * 2 + 1;
        if l >= n {
            break;
        }
        let mut best = l;
        let r = l + 1;
        if r < n && rt[r] > rt[best] {
            best = r;
        }
        if rt[i] < rt[best] {
            rt.swap(i, best);
            rn.swap(i, best);
            i = best;
        } else {
            break;
        }
    }
}

fn heapsort_ring(rt: &mut [i64], rn: &mut [i64], n: usize) {
    let mut start = n / 2;
    while start > 0 {
        start -= 1;
        sift_max_ring(rt, rn, start, n);
    }
    let mut end = n;
    while end > 1 {
        end -= 1;
        rt.swap(0, end);
        rn.swap(0, end);
        sift_max_ring(rt, rn, 0, end);
    }
}

fn build_ring(alive: &[i64], ring_tok: &mut [i64], ring_node: &mut [i64]) -> usize {
    const MAX_NODES: usize = 48;
    const VNODES: usize = 128;
    const GOLD_C: i64 = 2654435769;
    let mut sz = 0usize;
    for nid in 0..MAX_NODES {
        if alive[nid] == 1 {
            for v in 0..VNODES {
                ring_tok[sz] = mix32((((nid as i64) << 10) | (v as i64)) ^ GOLD_C);
                ring_node[sz] = nid as i64;
                sz += 1;
            }
        }
    }
    heapsort_ring(ring_tok, ring_node, sz);
    sz
}

fn route_tok(ring_tok: &[i64], ring_node: &[i64], tok: i64, sz: usize) -> i64 {
    let mut lo = 0usize;
    let mut hi = sz;
    while lo < hi {
        let mid = (lo + hi) >> 1;
        if ring_tok[mid] < tok {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    if lo == sz {
        lo = 0;
    }
    ring_node[lo]
}

fn main() {
    const MASK32: i64 = 4294967295;
    const MAX_NODES: usize = 48;
    const VNODES: usize = 128;
    const N_KEYS: usize = 150000;

    let mut alive = vec![0i64; MAX_NODES];
    let mut node_load = vec![0i64; MAX_NODES];
    for nid in 0..32 {
        alive[nid] = 1;
    }

    let mut ring_tok = vec![0i64; MAX_NODES * VNODES];
    let mut ring_node = vec![0i64; MAX_NODES * VNODES];
    let mut key_tok = vec![0i64; N_KEYS];
    let mut prev_owner = vec![0i64; N_KEYS];

    for i in 0..N_KEYS {
        key_tok[i] = mix32(((i as i64) * 2654435761 + 12345) & MASK32);
    }

    let mut ring_sz = build_ring(&alive, &mut ring_tok, &mut ring_node);
    let mut ck: i64 = 0;
    for p in 0i64..4 {
        let salt = p * 7919;
        for i in 0..N_KEYS {
            let t = mix32((key_tok[i] + salt) & MASK32);
            let owner = route_tok(&ring_tok, &ring_node, t, ring_sz);
            node_load[owner as usize] += 1;
            ck = (ck * 31 + owner + 1) % MOD_V;
        }
    }

    for i in 0..N_KEYS {
        prev_owner[i] = route_tok(&ring_tok, &ring_node, key_tok[i], ring_sz);
    }

    let mut total_moved: i64 = 0;
    for step in 0..4 {
        if step == 0 {
            alive[32] = 1; alive[33] = 1; alive[34] = 1; alive[35] = 1;
        } else if step == 1 {
            alive[5] = 0; alive[19] = 0;
        } else if step == 2 {
            alive[36] = 1; alive[37] = 1; alive[38] = 1; alive[39] = 1; alive[40] = 1; alive[41] = 1;
        } else {
            alive[2] = 0; alive[11] = 0; alive[24] = 0; alive[33] = 0;
        }
        ring_sz = build_ring(&alive, &mut ring_tok, &mut ring_node);
        let mut moved: i64 = 0;
        for i in 0..N_KEYS {
            let o = route_tok(&ring_tok, &ring_node, key_tok[i], ring_sz);
            if o != prev_owner[i] {
                moved += 1;
                prev_owner[i] = o;
            }
            ck = (ck * 31 + o + 1) % MOD_V;
        }
        total_moved += moved;
        ck = (ck * 37 + moved) % MOD_V;
    }

    for nid in 0..MAX_NODES {
        ck = (ck * 31 + node_load[nid]) % MOD_V;
    }

    println!("{}\n{}", total_moved, ck);
}
