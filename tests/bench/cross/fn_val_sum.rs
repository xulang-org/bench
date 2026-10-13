fn bump(x: i64) -> i64 {
    x + 1
}

fn main() {
    let f: fn(i64) -> i64 = bump;
    let mut s: i64 = 0;
    let mut i: i64 = 0;
    while i < 8_000_000 {
        s += f(i & 7);
        i += 1;
    }
    println!("{}", s);
}
