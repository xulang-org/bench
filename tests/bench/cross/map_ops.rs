use std::collections::HashMap;

fn main() {
    let mut m: HashMap<i64, i64> = HashMap::new();
    let mut i: i64 = 0;
    while i < 200_000 {
        m.insert(i, 1);
        i += 1;
    }
    let mut s: i64 = 0;
    i = 0;
    while i < 200_000 {
        s += m[&i] + i;
        i += 1;
    }
    println!("{}", s);
}
