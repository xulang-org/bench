// Osprey (MIT): benchmarks/cases/coins; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Unmemoised SICP change counting: amount 600, denominations 1/5/10/25/50.

fn coin(k: i64) -> i64 {
    if k == 1 { return 1; }
    if k == 2 { return 5; }
    if k == 3 { return 10; }
    if k == 4 { return 25; }
    return 50;
}
fn ways(amount: i64, kind: i64) -> i64 {
    if amount == 0 { return 1; }
    if amount < 0 { return 0; }
    if kind == 0 { return 0; }
    return ways(amount - coin(kind), kind) + ways(amount, kind - 1);
}

fn main() {
    let result: i64 = ways(600, 5);
    println!("{}", result);
}
