fn main() {
    let mut a: Vec<i64> = Vec::new();
    let mut i: i64 = 0;
    while i < 2_000_000 {
        a.push(i);
        i += 1;
    }
    let mut s: i64 = 0;
    let mut j: i64 = 0;
    let n = a.len() as i64;
    while j < n {
        s += a[j as usize] & 7;
        j += 1;
    }
    println!("{}", s);
}
