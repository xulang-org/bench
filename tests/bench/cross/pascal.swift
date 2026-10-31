// Osprey (MIT): benchmarks/cases/pascal; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Unmemoised Pascal recursion: binomial coefficient C(27,13).

func binom(_ n: Int64, _ k: Int64) -> Int64 {
    if k == 0 { return 1 }
    if k == n { return 1 }
    return binom(n - 1, k - 1) + binom(n - 1, k)
}

func main() {
    var result: Int64 = binom(27, 13)
    print(result)
}

main()
