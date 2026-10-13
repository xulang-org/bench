use std::fs;

const N: usize = 524_288;
const ROUNDS: usize = 32;

fn main() {
    let payload = vec![b'A'; N];
    let mut sum: i64 = 0;
    for _ in 0..ROUNDS {
        fs::write("roundtrip.bin", &payload).unwrap();
        let got = fs::read("roundtrip.bin").unwrap();
        if got != payload {
            std::process::exit(1);
        }
        sum += got[0] as i64 + got[N / 2] as i64 + got[N - 1] as i64;
    }
    println!("{}", sum);
}
