fn main() {
    let mut s: i64 = 0;
    let mut i: i64 = 0;
    while i < 24_000_000 {
        match i & 7 {
            0 => s += 1,
            1 => s += 3,
            2 => s += 5,
            3 => s += 7,
            4 => s += 11,
            5 => s += 13,
            6 => s += 17,
            _ => s += 19,
        }
        i += 1;
    }
    println!("{}", s);
    println!("{}", i);
}
