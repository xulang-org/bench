fn main() {
    let mut a: Vec<i64> = Vec::new();
    let mut i: i64 = 0;
    let mut x: i64 = 12345;
    while i < 100_000 {
        x = (x * 1_103_515_245 + 12345) & 0x7FFF_FFFF;
        a.push(x);
        i += 1;
    }
    a.sort_unstable();
    println!("{}", a[0] + a[50_000] * 2 + a[99_999] * 3);
}
