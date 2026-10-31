// Osprey (MIT): benchmarks/cases/coins; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Unmemoised SICP change counting: amount 600, denominations 1/5/10/25/50.

func coin(_ k: Int64) -> Int64 {
    if k == 1 { return 1 }
    if k == 2 { return 5 }
    if k == 3 { return 10 }
    if k == 4 { return 25 }
    return 50
}
func ways(_ amount: Int64, _ kind: Int64) -> Int64 {
    if amount == 0 { return 1 }
    if amount < 0 { return 0 }
    if kind == 0 { return 0 }
    return ways(amount - coin(kind), kind) + ways(amount, kind - 1)
}

func main() {
    var result: Int64 = ways(600, 5)
    print(result)
}

main()
