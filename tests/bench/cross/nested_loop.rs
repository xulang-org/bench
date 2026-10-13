fn main() {
    let mut s: i64 = 0;
    let mut i: i64 = 0;
    while i < 8000 {
        let mut j: i64 = 0;
        while j < 8000 {
            s += (i * j) & 1023;
            j += 1;
        }
        i += 1;
    }
    println!("{}", s);
}
