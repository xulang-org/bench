// Osprey (MIT): benchmarks/cases/mutual; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Mutually recursive parity, i%1000 for 1 <= i < 130000.

fn even(n: i64) -> i64 {
    if n == 0 { return 1; }
    return odd(n - 1);
}
fn odd(n: i64) -> i64 {
    if n == 0 { return 0; }
    return even(n - 1);
}

fn main() {
    let mut result: i64 = 0;
    let mut i: i64 = 1;
    while i < 130000 {
        result += even(i % 1000);
        i += 1;
    }
    println!("{}", result);
}
