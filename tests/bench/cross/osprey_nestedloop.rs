// Osprey (MIT): benchmarks/cases/nestedloop; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Osprey nestedloop: descending 250^3 modular multiply/adds.

fn loop_k(i: i64, j: i64, n: i64, initial: i64) -> i64 {
    let mut k: i64 = n;
    let mut acc: i64 = initial;
    while k != 0 {
        acc = (acc + i * j * k) % 1000000007;
        k -= 1;
    }
    return acc;
}
fn loop_j(i: i64, n: i64, initial: i64) -> i64 {
    let mut j: i64 = n;
    let mut acc: i64 = initial;
    while j != 0 {
        acc = loop_k(i, j, n, acc);
        j -= 1;
    }
    return acc;
}
fn loop_i(n: i64) -> i64 {
    let mut i: i64 = n;
    let mut acc: i64 = 0;
    while i != 0 {
        acc = loop_j(i, n, acc);
        i -= 1;
    }
    return acc;
}

fn main() {
    let result: i64 = loop_i(250);
    println!("{}", result);
}
