struct AVL {
    keys: Vec<i64>,
    vals: Vec<i64>,
    heights: Vec<i32>,
    lefts: Vec<i32>,
    rights: Vec<i32>,
    count: usize,
    root: i32,
}

impl AVL {
    fn new(cap: usize) -> Self {
        AVL {
            keys: vec![0; cap],
            vals: vec![0; cap],
            heights: vec![0; cap],
            lefts: vec![-1; cap],
            rights: vec![-1; cap],
            count: 0,
            root: -1,
        }
    }

    #[inline(always)]
    fn get_h(&self, idx: i32) -> i32 {
        if idx == -1 { 0 } else { self.heights[idx as usize] }
    }

    #[inline(always)]
    fn upd(&mut self, idx: i32) {
        let u = idx as usize;
        let hl = self.get_h(self.lefts[u]);
        let hr = self.get_h(self.rights[u]);
        self.heights[u] = 1 + (if hl > hr { hl } else { hr });
    }

    #[inline(always)]
    fn bf(&self, idx: i32) -> i32 {
        let u = idx as usize;
        self.get_h(self.lefts[u]) - self.get_h(self.rights[u])
    }

    fn rot_r(&mut self, y: i32) -> i32 {
        let yu = y as usize;
        let x = self.lefts[yu];
        let xu = x as usize;
        let t2 = self.rights[xu];
        self.rights[xu] = y;
        self.lefts[yu] = t2;
        self.upd(y);
        self.upd(x);
        x
    }

    fn rot_l(&mut self, x: i32) -> i32 {
        let xu = x as usize;
        let y = self.rights[xu];
        let yu = y as usize;
        let t2 = self.lefts[yu];
        self.lefts[yu] = x;
        self.rights[xu] = t2;
        self.upd(x);
        self.upd(y);
        y
    }

    fn insert(&mut self, idx: i32, key: i64, val: i64) -> i32 {
        if idx == -1 {
            let nid = self.count as i32;
            self.count += 1;
            let nu = nid as usize;
            self.keys[nu] = key;
            self.vals[nu] = val;
            self.heights[nu] = 1;
            self.lefts[nu] = -1;
            self.rights[nu] = -1;
            return nid;
        }
        let u = idx as usize;
        if key < self.keys[u] {
            let l = self.lefts[u];
            self.lefts[u] = self.insert(l, key, val);
        } else if key > self.keys[u] {
            let r = self.rights[u];
            self.rights[u] = self.insert(r, key, val);
        } else {
            self.vals[u] = val;
            return idx;
        }
        self.upd(idx);
        let b = self.bf(idx);
        if b > 1 && key < self.keys[self.lefts[u] as usize] {
            return self.rot_r(idx);
        }
        if b < -1 && key > self.keys[self.rights[u] as usize] {
            return self.rot_l(idx);
        }
        if b > 1 && key > self.keys[self.lefts[u] as usize] {
            let l = self.lefts[u];
            self.lefts[u] = self.rot_l(l);
            return self.rot_r(idx);
        }
        if b < -1 && key < self.keys[self.rights[u] as usize] {
            let r = self.rights[u];
            self.rights[u] = self.rot_r(r);
            return self.rot_l(idx);
        }
        idx
    }

    fn search(&self, key: i64) -> i64 {
        let mut cur = self.root;
        while cur != -1 {
            let u = cur as usize;
            let k = self.keys[u];
            if key == k {
                return self.vals[u];
            } else if key < k {
                cur = self.lefts[u];
            } else {
                cur = self.rights[u];
            }
        }
        0
    }
}

fn main() {
    let mut t = AVL::new(100000);
    let mut seed = 123456789i64;
    for i in 0..80000 {
        seed = (seed * 1103515245 + 12345) & 0x7fffffff;
        let k = seed % 200000;
        let v = (i * 3 + 7) & 0x7fffffff;
        t.root = t.insert(t.root, k, v);
    }

    let mut checksum = 0i64;
    for _ in 0..300000 {
        seed = (seed * 1103515245 + 12345) & 0x7fffffff;
        let k = seed % 200000;
        let val = t.search(k);
        checksum = (checksum * 31 + val) % 1000000007;
    }
    println!("{}", checksum);
}
