fn main() {
    let mut b: Vec<u8> = Vec::with_capacity(64);
    let mut i: i64 = 0;
    while i < 100000 {
        b.push((48 + (i % 10)) as u8);
        i += 1;
    }
    let mut c: i64 = 0;
    let mut j: usize = 0;
    let n = b.len();
    while j < n {
        c += b[j] as i64;
        j += 1;
    }
    println!("{}\n{}", c, n);
}
