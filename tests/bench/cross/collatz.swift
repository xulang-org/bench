// Osprey (MIT): benchmarks/cases/collatz; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Recursive Collatz stopping times, summed over 1..100000.

func steps(_ n: Int64) -> Int64 {
    if n == 1 { return 0 }
    if n % 2 == 0 { return 1 + steps(n / 2) }
    return 1 + steps(3 * n + 1)
}

func main() {
    var result: Int64 = 0
    var i: Int64 = 1
    while i <= 100000 {
        result += steps(i)
        i += 1
    }
    print(result)
}

main()
