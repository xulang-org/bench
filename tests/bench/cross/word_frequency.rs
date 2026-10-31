// Osprey (MIT): benchmarks/cases/wordfreq; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// String-keyed frequency map, 200000 tokens, deterministic seed=1.
// Every token performs a map lookup followed by an update (not an indexed counter).
// Eight immutable ASCII keys; weighted final counts; see tests/bench/osprey/README.md.

use std::collections::HashMap;

fn hash_at(seed: i64, i: i64) -> i64 {
    (((seed + i) * 16807) % 2147483647 * 16807) % 2147483647
}

fn word(k: i64) -> &'static str {
    if k == 0 { return "the"; }
    if k == 1 { return "quick"; }
    if k == 2 { return "brown"; }
    if k == 3 { return "fox"; }
    if k == 4 { return "jumps"; }
    if k == 5 { return "over"; }
    if k == 6 { return "lazy"; }
    "dog"
}

fn main() {
    let mut counts: HashMap<&str, i64> = HashMap::new();
    let mut i: i64 = 0;
    while i < 200000 {
        let w = word(hash_at(1, i) % 8);
        let count = counts.get(w).copied().unwrap_or(0);
        counts.insert(w, count + 1);
        i += 1;
    }
    let mut result: i64 = 0;
    i = 0;
    while i < 8 {
        result += (i + 1) * counts.get(word(i)).copied().unwrap_or(0);
        i += 1;
    }
    println!("{}", result);
}
