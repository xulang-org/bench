struct Node {
    key: i64,
    val: i64,
    prev: i32,
    next: i32,
}

struct LRU {
    nodes: Vec<Node>,
    table: Vec<i32>,
    head: i32,
    tail: i32,
    cap: i32,
    count: i32,
}

impl LRU {
    fn new(cap: usize, table_size: usize) -> Self {
        let mut nodes = Vec::with_capacity(cap);
        for _ in 0..cap {
            nodes.push(Node {
                key: -1,
                val: 0,
                prev: -1,
                next: -1,
            });
        }
        Self {
            nodes,
            table: vec![-1; table_size],
            head: -1,
            tail: -1,
            cap: cap as i32,
            count: 0,
        }
    }

    fn remove_node(&mut self, idx: i32) {
        let p = self.nodes[idx as usize].prev;
        let n = self.nodes[idx as usize].next;
        if p >= 0 {
            self.nodes[p as usize].next = n;
        } else {
            self.head = n;
        }
        if n >= 0 {
            self.nodes[n as usize].prev = p;
        } else {
            self.tail = p;
        }
    }

    fn push_front(&mut self, idx: i32) {
        self.nodes[idx as usize].prev = -1;
        self.nodes[idx as usize].next = self.head;
        if self.head >= 0 {
            self.nodes[self.head as usize].prev = idx;
        }
        self.head = idx;
        if self.tail < 0 {
            self.tail = idx;
        }
    }

    fn put(&mut self, key: i64, val: i64) -> i64 {
        let old_idx = self.table[key as usize];
        if old_idx >= 0 {
            self.nodes[old_idx as usize].val = val;
            self.remove_node(old_idx);
            self.push_front(old_idx);
            return val;
        }
        let idx = if self.count < self.cap {
            let i = self.count;
            self.count += 1;
            i
        } else {
            let i = self.tail;
            let old_key = self.nodes[i as usize].key;
            self.table[old_key as usize] = -1;
            self.remove_node(i);
            i
        };
        self.nodes[idx as usize].key = key;
        self.nodes[idx as usize].val = val;
        self.table[key as usize] = idx;
        self.push_front(idx);
        val
    }

    fn get(&mut self, key: i64) -> i64 {
        let idx = self.table[key as usize];
        if idx < 0 {
            return -1;
        }
        self.remove_node(idx);
        self.push_front(idx);
        self.nodes[idx as usize].val
    }
}

fn main() {
    let mut lru = LRU::new(1000, 3000);
    let mut seed: i64 = 123456789;
    let mut checksum: i64 = 0;

    for _ in 0..2500000 {
        seed = (seed * 1664525 + 1013904223) % 2147483647;
        let key = seed % 3000;
        let val = seed % 1000000;
        if (seed & 1) == 0 {
            let res = lru.put(key, val);
            checksum = (checksum * 33 + res) % 1000000007;
        } else {
            let res = lru.get(key);
            checksum = (checksum * 33 + res) % 1000000007;
        }
    }

    println!("{}", checksum);
}
