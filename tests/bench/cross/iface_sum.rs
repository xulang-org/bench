trait Src {
    fn val(&self) -> i64;
}

struct A {
    x: i64,
}

struct B {
    x: i64,
}

impl Src for A {
    fn val(&self) -> i64 {
        self.x
    }
}

impl Src for B {
    fn val(&self) -> i64 {
        self.x * 2
    }
}

fn main() {
    let a = A { x: 1 };
    let b = B { x: 2 };
    let xs: [&dyn Src; 2] = [&a, &b];
    let mut s: i64 = 0;
    let mut i: i64 = 0;
    while i < 8_000_000 {
        s += xs[(i & 1) as usize].val();
        i += 1;
    }
    println!("{}", s);
}
