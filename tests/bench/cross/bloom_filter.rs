struct BloomFilter {
    bits: Vec<u64>,
    mask: u64,
}

impl BloomFilter {
    fn new(num_bits: usize) -> Self {
        Self {
            bits: vec![0; num_bits / 64],
            mask: (num_bits - 1) as u64,
        }
    }

    fn add(&mut self, val: i64) {
        let h1 = (val * 1103515245 + 12345) & 2147483647;
        let h2 = (val * 1664525 + 1013904223) & 2147483647;
        for i in 0..4 {
            let bit = ((h1 + i * h2) as u64) & self.mask;
            self.bits[(bit >> 6) as usize] |= 1 << (bit & 63);
        }
    }

    fn contains(&self, val: i64) -> bool {
        let h1 = (val * 1103515245 + 12345) & 2147483647;
        let h2 = (val * 1664525 + 1013904223) & 2147483647;
        for i in 0..4 {
            let bit = ((h1 + i * h2) as u64) & self.mask;
            if (self.bits[(bit >> 6) as usize] & (1 << (bit & 63))) == 0 {
                return false;
            }
        }
        true
    }
}

fn main() {
    let mut bf = BloomFilter::new(1048576);
    let mut seed: i64 = 123456789;

    for _ in 0..200000 {
        seed = (seed * 1664525 + 1013904223) % 2147483647;
        bf.add(seed);
    }

    let mut checksum: i64 = 0;
    for _ in 0..2000000 {
        seed = (seed * 1664525 + 1013904223) % 2147483647;
        if bf.contains(seed) {
            checksum = (checksum * 31 + seed) % 1000000007;
        }
    }

    println!("{}", checksum);
}
