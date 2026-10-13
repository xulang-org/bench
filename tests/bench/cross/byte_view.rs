fn main() {
    let mut s = String::with_capacity(100000);
    let mut i: i64 = 0;
    while i < 10000 {
        s.push_str("0123456789");
        i += 1;
    }
    let mut hits: i64 = 0;
    let mut k: i64 = 0;
    while k < 20 {
        if s.as_bytes().contains(&b'9') {
            hits += 1;
        }
        if s.contains("89012") {
            hits += 1;
        }
        k += 1;
    }
    println!("{}\n{}", hits, s.len());
}
