fn main() {
    let mut s: i64 = 0;
    let mut i: i64 = 0;
    while i < 50_000_000 {
        s += i & 1023;
        i += 1;
    }
    println!("{}", s);
}
