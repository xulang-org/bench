fn main() {
    let mut pool: Vec<String> = Vec::new(); let mut si: i64 = 0;
    while si < 32 {
        let n = 8 + si % 24; let mut bytes = Vec::new(); let mut j: i64 = 0;
        while j < n { bytes.push((97 + (j + si) % 3) as u8); j += 1; }
        pool.push(String::from_utf8(bytes).unwrap()); si += 1;
    }
    let mut state: i64 = 1; let mut total: i64 = 0; let mut i: i64 = 0;
    while i < 1000000 {
        state = (state * 1103515245 + 12345) & 2147483647;
        let idx = ((state >> 16) & 31) as usize; let needle = (97 + ((state >> 8) & 1)) as u8;
        let s = pool[idx].as_bytes(); let mut count: i64 = 0; let mut j: usize = 0;
        while j < s.len() { count += (s[j] == needle) as i64; j += 1; }
        total += count; i += 1;
    }
    println!("{}", total);
}
