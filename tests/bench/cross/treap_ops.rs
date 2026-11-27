struct Pair {
    l: i64,
    r: i64,
}

struct Treap {
    key: Vec<i64>,
    pri: Vec<i64>,
    left: Vec<i64>,
    right: Vec<i64>,
    free_head: i64,
    root: i64,
    size: i64,
}

impl Treap {
    fn new() -> Self {
        Self {
            key: Vec::with_capacity(32768),
            pri: Vec::with_capacity(32768),
            left: Vec::with_capacity(32768),
            right: Vec::with_capacity(32768),
            free_head: -1,
            root: -1,
            size: 0,
        }
    }

    fn alloc_node(&mut self, k: i64, p: i64) -> i64 {
        if self.free_head != -1 {
            let idx = self.free_head;
            let iu = idx as usize;
            self.free_head = self.left[iu];
            self.key[iu] = k;
            self.pri[iu] = p;
            self.left[iu] = -1;
            self.right[iu] = -1;
            return idx;
        }
        let idx = self.key.len() as i64;
        self.key.push(k);
        self.pri.push(p);
        self.left.push(-1);
        self.right.push(-1);
        idx
    }

    fn free_node(&mut self, idx: i64) {
        let iu = idx as usize;
        self.left[iu] = self.free_head;
        self.right[iu] = -1;
        self.free_head = idx;
    }

    fn split(&mut self, u: i64, k: i64) -> Pair {
        if u == -1 {
            return Pair { l: -1, r: -1 };
        }
        let uu = u as usize;
        if self.key[uu] < k {
            let ru = self.right[uu];
            let p = self.split(ru, k);
            self.right[uu] = p.l;
            return Pair { l: u, r: p.r };
        }
        let lu = self.left[uu];
        let p = self.split(lu, k);
        self.left[uu] = p.r;
        Pair { l: p.l, r: u }
    }

    fn merge(&mut self, a: i64, b: i64) -> i64 {
        if a == -1 {
            return b;
        }
        if b == -1 {
            return a;
        }
        let au = a as usize;
        let bu = b as usize;
        if self.pri[au] > self.pri[bu] {
            let ra = self.right[au];
            let m = self.merge(ra, b);
            self.right[au] = m;
            return a;
        }
        let lb = self.left[bu];
        let m = self.merge(a, lb);
        self.left[bu] = m;
        b
    }

    fn contains(&self, k: i64) -> bool {
        let mut u = self.root;
        while u != -1 {
            let uu = u as usize;
            let ku = self.key[uu];
            if k == ku {
                return true;
            }
            u = if k < ku { self.left[uu] } else { self.right[uu] };
        }
        false
    }

    fn insert(&mut self, k: i64, p: i64) {
        if self.contains(k) {
            return;
        }
        let root = self.root;
        let sp = self.split(root, k);
        let n = self.alloc_node(k, p);
        let m1 = self.merge(sp.l, n);
        self.root = self.merge(m1, sp.r);
        self.size += 1;
    }

    fn erase(&mut self, k: i64) {
        let root = self.root;
        let sp1 = self.split(root, k);
        let sp2 = self.split(sp1.r, k + 1);
        if sp2.l != -1 {
            self.free_node(sp2.l);
            self.size -= 1;
        }
        self.root = self.merge(sp1.l, sp2.r);
    }
}

fn main() {
    let mut tr = Treap::new();
    let mut rng: i64 = 123456789;
    let mut hits: i64 = 0;
    let mut ck: i64 = 0;
    for _ in 0..120000 {
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let op = rng % 10;
        rng = (rng * 1103515245 + 12345) & 2147483647;
        let k = rng % 40000;
        if op < 4 {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            tr.insert(k, rng);
        } else if op < 6 {
            tr.erase(k);
        } else if tr.contains(k) {
            hits += 1;
            ck = (ck * 131 + k + 1) % 1000000007;
        }
    }
    println!("{}\n{}\n{}", hits, ck, tr.size);
}
