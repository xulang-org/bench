struct Deque {
    buf: Vec<i64>,
    head: usize,
    tail: usize,
    count: usize,
    mask: usize,
}

impl Deque {
    fn new() -> Self {
        Self {
            buf: vec![0; 16],
            head: 0,
            tail: 0,
            count: 0,
            mask: 15,
        }
    }

    fn grow(&mut self) {
        let old_cap = self.mask + 1;
        let old_mask = self.mask;
        let new_cap = old_cap * 2;
        let mut new_buf = vec![0; new_cap];
        for j in 0..self.count {
            new_buf[j] = self.buf[(self.head + j) & old_mask];
        }
        self.buf = new_buf;
        self.head = 0;
        self.tail = self.count;
        self.mask = new_cap - 1;
    }

    fn push_back(&mut self, val: i64) {
        if self.count == self.mask + 1 {
            self.grow();
        }
        self.buf[self.tail] = val;
        self.tail = (self.tail + 1) & self.mask;
        self.count += 1;
    }

    fn push_front(&mut self, val: i64) {
        if self.count == self.mask + 1 {
            self.grow();
        }
        self.head = self.head.wrapping_sub(1) & self.mask;
        self.buf[self.head] = val;
        self.count += 1;
    }

    fn pop_front(&mut self) -> i64 {
        if self.count == 0 {
            return 0;
        }
        let val = self.buf[self.head];
        self.head = (self.head + 1) & self.mask;
        self.count -= 1;
        val
    }

    fn pop_back(&mut self) -> i64 {
        if self.count == 0 {
            return 0;
        }
        self.tail = self.tail.wrapping_sub(1) & self.mask;
        let val = self.buf[self.tail];
        self.count -= 1;
        val
    }
}

fn main() {
    let mut q = Deque::new();
    let mut seed: i64 = 123456789;
    let mut checksum: i64 = 0;

    for _ in 0..5000000 {
        seed = (seed * 1664525 + 1013904223) % 2147483647;
        let op = seed % 4;
        if op == 0 {
            q.push_back(seed);
        } else if op == 1 {
            q.push_front(seed);
        } else if op == 2 {
            let v = q.pop_front();
            checksum = (checksum * 33 + v) % 1000000007;
        } else {
            let v = q.pop_back();
            checksum = (checksum * 33 + v) % 1000000007;
        }
    }

    while q.count > 0 {
        let v = q.pop_front();
        checksum = (checksum * 33 + v) % 1000000007;
    }

    println!("{}", checksum);
}
