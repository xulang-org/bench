const MOD_V: i64 = 1000000007;

struct BPlusTree {
    is_leaf: Vec<i64>,
    nkeys: Vec<usize>,
    next_leaf: Vec<i64>,
    keys: Vec<i64>,
    vals: Vec<i64>,
    children: Vec<i64>,
    path_node: [usize; 16],
    path_idx: [usize; 16],
    root: usize,
}

impl BPlusTree {
    fn new() -> Self {
        let mut t = Self {
            is_leaf: Vec::new(),
            nkeys: Vec::new(),
            next_leaf: Vec::new(),
            keys: Vec::new(),
            vals: Vec::new(),
            children: Vec::new(),
            path_node: [0usize; 16],
            path_idx: [0usize; 16],
            root: 0,
        };
        t.root = t.alloc_node(1);
        t
    }

    fn alloc_node(&mut self, leaf: i64) -> usize {
        let u = self.is_leaf.len();
        self.is_leaf.push(leaf);
        self.nkeys.push(0);
        self.next_leaf.push(-1);
        for _ in 0..32 {
            self.keys.push(0);
            self.vals.push(0);
        }
        for _ in 0..33 {
            self.children.push(-1);
        }
        u
    }

    fn descend_leaf(&self, k: i64) -> usize {
        let mut u = self.root;
        while self.is_leaf[u] == 0 {
            let base = u * 32;
            let mut lo = 0usize;
            let mut hi = self.nkeys[u];
            while lo < hi {
                let mid = (lo + hi) >> 1;
                if self.keys[base + mid] <= k {
                    lo = mid + 1;
                } else {
                    hi = mid;
                }
            }
            u = self.children[u * 33 + lo] as usize;
        }
        u
    }

    fn insert(&mut self, k: i64, v: i64) {
        let mut u = self.root;
        let mut depth = 0usize;
        while self.is_leaf[u] == 0 {
            let base = u * 32;
            let mut lo = 0usize;
            let mut hi = self.nkeys[u];
            while lo < hi {
                let mid = (lo + hi) >> 1;
                if self.keys[base + mid] <= k {
                    lo = mid + 1;
                } else {
                    hi = mid;
                }
            }
            self.path_node[depth] = u;
            self.path_idx[depth] = lo;
            depth += 1;
            u = self.children[u * 33 + lo] as usize;
        }

        let base = u * 32;
        let mut n = self.nkeys[u];
        let mut lo = 0usize;
        let mut hi = n;
        while lo < hi {
            let mid = (lo + hi) >> 1;
            if self.keys[base + mid] < k {
                lo = mid + 1;
            } else {
                hi = mid;
            }
        }
        if lo < n && self.keys[base + lo] == k {
            self.vals[base + lo] = v;
            return;
        }
        let mut j = n;
        while j > lo {
            self.keys[base + j] = self.keys[base + j - 1];
            self.vals[base + j] = self.vals[base + j - 1];
            j -= 1;
        }
        self.keys[base + lo] = k;
        self.vals[base + lo] = v;
        n += 1;
        self.nkeys[u] = n;
        if n < 32 {
            return;
        }

        let r = self.alloc_node(1);
        let rbase = r * 32;
        for m in 0..16 {
            self.keys[rbase + m] = self.keys[base + 16 + m];
            self.vals[rbase + m] = self.vals[base + 16 + m];
        }
        self.nkeys[u] = 16;
        self.nkeys[r] = 16;
        self.next_leaf[r] = self.next_leaf[u];
        self.next_leaf[u] = r as i64;
        let mut up_key = self.keys[rbase];
        let mut up_right = r as i64;

        let mut d = depth;
        while d > 0 {
            d -= 1;
            let p = self.path_node[d];
            let ins = self.path_idx[d];
            let pbase = p * 32;
            let pcbase = p * 33;
            let mut pn = self.nkeys[p];
            let mut k_idx = pn;
            while k_idx > ins {
                self.keys[pbase + k_idx] = self.keys[pbase + k_idx - 1];
                self.children[pcbase + k_idx + 1] = self.children[pcbase + k_idx];
                k_idx -= 1;
            }
            self.keys[pbase + ins] = up_key;
            self.children[pcbase + ins + 1] = up_right;
            pn += 1;
            self.nkeys[p] = pn;
            if pn < 32 {
                return;
            }
            let nr = self.alloc_node(0);
            let nrbase = nr * 32;
            let nrcbase = nr * 33;
            let mid_key = self.keys[pbase + 16];
            for m in 0..15 {
                self.keys[nrbase + m] = self.keys[pbase + 17 + m];
            }
            for c in 0..16 {
                self.children[nrcbase + c] = self.children[pcbase + 17 + c];
            }
            self.nkeys[p] = 16;
            self.nkeys[nr] = 15;
            up_key = mid_key;
            up_right = nr as i64;
        }

        let new_root = self.alloc_node(0);
        self.keys[new_root * 32] = up_key;
        self.children[new_root * 33] = self.root as i64;
        self.children[new_root * 33 + 1] = up_right;
        self.nkeys[new_root] = 1;
        self.root = new_root;
    }

    fn lookup(&self, k: i64) -> i64 {
        let u = self.descend_leaf(k);
        let base = u * 32;
        let n = self.nkeys[u];
        let mut lo = 0usize;
        let mut hi = n;
        while lo < hi {
            let mid = (lo + hi) >> 1;
            if self.keys[base + mid] < k {
                lo = mid + 1;
            } else {
                hi = mid;
            }
        }
        if lo < n && self.keys[base + lo] == k {
            return self.vals[base + lo];
        }
        -1
    }
}

fn main() {
    let mut t = BPlusTree::new();
    let mut rng: i64 = 123456789;

    for i in 0i64..80000 {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let k = rng % 1000000;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let v = (i * 17 + (rng & 1023)) % 1000000;
        t.insert(k, v);
    }

    let mut hits: i64 = 0;
    let mut ck: i64 = 0;
    for _ in 0..120000 {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let k = rng % 1000000;
        let v = t.lookup(k);
        if v >= 0 {
            hits += 1;
            ck = (ck * 31 + v) % MOD_V;
        }
    }

    let mut rcnt: i64 = 0;
    for _ in 0..2000 {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let lo_k = rng % 999000;
        let hi_k = lo_k + 1000;
        let mut u = t.descend_leaf(lo_k) as i64;
        let u0 = u as usize;
        let base0 = u0 * 32;
        let mut lo = 0usize;
        let mut hi = t.nkeys[u0];
        while lo < hi {
            let mid = (lo + hi) >> 1;
            if t.keys[base0 + mid] < lo_k {
                lo = mid + 1;
            } else {
                hi = mid;
            }
        }
        let mut cnt: i64 = 0;
        let mut s: i64 = 0;
        let mut idx = lo;
        while u != -1 {
            let uu = u as usize;
            let base = uu * 32;
            let n = t.nkeys[uu];
            let mut done = false;
            for j in idx..n {
                if t.keys[base + j] > hi_k {
                    done = true;
                    break;
                }
                cnt += 1;
                s = (s + t.vals[base + j]) % MOD_V;
            }
            if done {
                break;
            }
            u = t.next_leaf[uu];
            idx = 0;
        }
        rcnt += cnt;
        ck = (ck * 37 + s + cnt) % MOD_V;
    }

    println!("{}\n{}", hits + rcnt, ck);
}
