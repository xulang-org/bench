fn main() {
    let mut s: f64 = 0.0;
    let mut i: i64 = 0;
    while i < 20_000_000 {
        s += (i & 1023) as f64;
        i += 1;
    }
    println!("{}", s as i64);
}
