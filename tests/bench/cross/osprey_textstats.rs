// Osprey (MIT): benchmarks/cases/textstats; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.



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

fn score(w: &str) -> i64 {
    let mut result = w.len() as i64;
    if w.contains('o') { result += 7; }
    if w.starts_with('t') { result += 3; }
    result
}

fn main() {
    let mut result: i64 = 0;
    let mut i: i64 = 0;
    while i < 200000 {
        result += score(word(hash_at(1, i) % 8));
        i += 1;
    }
    println!("{}", result);
}
