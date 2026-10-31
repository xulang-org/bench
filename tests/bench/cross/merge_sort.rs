// Osprey (MIT): benchmarks/cases/mergesort; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Top-down merge sort with alternating split and fresh growable vectors.
// 8 rounds x 2000 values; seed=1+131*t, rank-weighted modular checksum.
// Identical split/merge/push loops in all ports; see tests/bench/osprey/README.md.

fn hash_at(seed: i64, i: i64) -> i64 {
    (((seed + i) * 16807) % 2147483647 * 16807) % 2147483647
}

fn merge(left: &[i64], right: &[i64]) -> Vec<i64> {
    let mut result = Vec::new();
    let mut i: i64 = 0;
    let mut j: i64 = 0;
    while i < left.len() as i64 && j < right.len() as i64 {
        if right[j as usize] < left[i as usize] {
            result.push(right[j as usize]);
            j += 1;
        } else {
            result.push(left[i as usize]);
            i += 1;
        }
    }
    while i < left.len() as i64 { result.push(left[i as usize]); i += 1; }
    while j < right.len() as i64 { result.push(right[j as usize]); j += 1; }
    result
}

fn merge_sort(xs: &[i64]) -> Vec<i64> {
    if xs.len() < 2 {
        let mut result = Vec::new();
        let mut i: i64 = 0;
        while i < xs.len() as i64 { result.push(xs[i as usize]); i += 1; }
        return result;
    }
    let mut evens = Vec::new();
    let mut odds = Vec::new();
    let mut i: i64 = 0;
    while i < xs.len() as i64 { evens.push(xs[i as usize]); i += 2; }
    i = 1;
    while i < xs.len() as i64 { odds.push(xs[i as usize]); i += 2; }
    let left = merge_sort(&evens);
    let right = merge_sort(&odds);
    merge(&left, &right)
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
        let sorted = merge_sort(&xs);
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
