fn main() {
    let mut s = String::new();
    let mut i: i64 = 0;
    while i < 100_000 {
        s.push_str("0123456789");
        i += 1;
    }
    let mut c: i64 = 0;
    let mut j: i64 = 0;
    let n = s.len() as i64;
    let bytes = s.as_bytes();
    while j < n {
        c += bytes[j as usize] as i64;
        j += 1;
    }
    println!("{}", c);
    println!("{}", n);
}
