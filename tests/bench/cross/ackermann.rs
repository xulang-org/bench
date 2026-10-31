// Osprey (MIT): benchmarks/cases/ackermann; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Ackermann(3,10): nested, data-dependent recursion.

fn add(a: i64, b: i64) -> i64 { return a + b; }
fn sub(a: i64, b: i64) -> i64 { return a - b; }
fn ack(m: i64, n: i64) -> i64 {
    if m == 0 { return add(n, 1); }
    if n == 0 { return ack(sub(m, 1), 1); }
    return ack(sub(m, 1), ack(m, sub(n, 1)));
}

fn main() {
    let result: i64 = ack(3, 10);
    println!("{}", result);
}
