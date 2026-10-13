fn main() {
    let n: i64 = 100_000;
    let mut data: Vec<i64> = Vec::with_capacity(n as usize);
    let mut seed: i64 = 123456789;
    let mut i: i64 = 0;
    while i < n {
        seed = (seed * 1103515245 + 12345) & 2147483647;
        data.push(seed & 255);
        i += 1;
    }
    let poly: i64 = 3988292384;
    let mask32: i64 = 4294967295;
    let mut total: i64 = 0;
    let mut round: i64 = 0;
    while round < 20 {
        let mut crc: i64 = mask32;
        let mut k: i64 = 0;
        while k < n {
            let b = data[k as usize];
            crc = crc ^ b;
            let mut bit: i64 = 0;
            while bit < 8 {
                if (crc & 1) != 0 {
                    crc = ((crc >> 1) & 2147483647) ^ poly;
                } else {
                    crc = (crc >> 1) & 2147483647;
                }
                bit += 1;
            }
            k += 1;
        }
        total += crc ^ mask32;
        round += 1;
    }
    println!("{}", total);
}
