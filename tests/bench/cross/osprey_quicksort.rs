// Osprey (MIT): benchmarks/cases/quicksort; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Osprey first-element-pivot quicksort; two partition passes and fresh vectors.
// 8 rounds x 2000 values; seed=1+131*t, rank-weighted modular checksum.
// Identical partition/concatenate/push loops in all ports; see tests/bench/osprey/README.md.

fn hash_at(seed: i64, i: i64) -> i64 {
    (((seed + i) * 16807) % 2147483647 * 16807) % 2147483647
}

fn quicksort(xs: &[i64]) -> Vec<i64> {
    if xs.is_empty() { return Vec::new(); }
    let pivot = xs[0];
    let mut below = Vec::new();
    let mut at_least = Vec::new();
    let mut i: i64 = 1;
    while i < xs.len() as i64 {
        if xs[i as usize] < pivot { below.push(xs[i as usize]); }
        i += 1;
    }
    i = 1;
    while i < xs.len() as i64 {
        if xs[i as usize] >= pivot { at_least.push(xs[i as usize]); }
        i += 1;
    }
    let mut sorted = quicksort(&below);
    sorted.push(pivot);
    let right = quicksort(&at_least);
    i = 0;
    while i < right.len() as i64 { sorted.push(right[i as usize]); i += 1; }
    sorted
}

fn main() {
    let mut total: i64 = 0;
    let mut t: i64 = 0;
    while t < 8 {
        let mut xs = Vec::new();
        let mut i: i64 = 0;
        while i < 2000 {
            xs.push(hash_at(1 + t * 131, i) % 100000);
            i += 1;
        }
        let sorted = quicksort(&xs);
        let mut weight: i64 = 0;
        i = 0;
        while i < sorted.len() as i64 {
            weight = (weight + sorted[i as usize] * (i + 1)) % 1000000007;
            i += 1;
        }
        total = (total + weight) % 1000000007;
        t += 1;
    }
    println!("{}", total);
}
