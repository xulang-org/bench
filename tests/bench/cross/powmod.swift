// Osprey (MIT): benchmarks/cases/powmod; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Sum i^20 mod 1000000007, 1 <= i < 1000000; twenty multiplies, no squaring.

func power(_ base: Int64, _ e: Int64, _ acc: Int64) -> Int64 {
    if e == 0 { return acc }
    return power(base, e - 1, (acc * base) % 1000000007)
}

func main() {
    var result: Int64 = 0
    var i: Int64 = 1
    while i < 1000000 {
        result = (result + power(i, 20, 1)) % 1000000007
        i += 1
    }
    print(result)
}

main()
