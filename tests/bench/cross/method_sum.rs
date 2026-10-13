struct Acc {
    n: i64,
}

impl Acc {
    fn add(&mut self, x: i64) {
        self.n += x;
    }
}

fn main() {
    let mut a = Acc { n: 0 };
    let mut i: i64 = 0;
    while i < 8_000_000 {
        a.add(i & 7);
        i += 1;
    }
    println!("{}", a.n);
}
