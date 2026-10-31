// Osprey (MIT): benchmarks/cases/hanoi; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Accumulator-threaded double recursion for 25 Hanoi disks; count moves.

func moves(_ n: Int64, _ acc: Int64) -> Int64 {
    if n == 0 { return acc }
    return moves(n - 1, moves(n - 1, acc) + 1)
}

func main() {
    var result: Int64 = moves(25, 0)
    print(result)
}

main()
