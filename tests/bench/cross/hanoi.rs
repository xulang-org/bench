// Osprey (MIT): benchmarks/cases/hanoi; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Accumulator-threaded double recursion for 25 Hanoi disks; count moves.

fn moves(n: i64, acc: i64) -> i64 {
    if n == 0 { return acc; }
    return moves(n - 1, moves(n - 1, acc) + 1);
}

fn main() {
    let result: i64 = moves(25, 0);
    println!("{}", result);
}
