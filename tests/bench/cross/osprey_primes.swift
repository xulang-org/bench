// Osprey (MIT): benchmarks/cases/primes; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Osprey primes: trial division, every candidate divisor from 2 through sqrt(n).

func has_factor(_ n: Int64, _ d: Int64) -> Int64 {
    if d * d > n { return 0 }
    if n % d == 0 { return 1 }
    return has_factor(n, d + 1)
}
func is_prime(_ n: Int64) -> Int64 {
    if n < 2 { return 0 }
    return 1 - has_factor(n, 2)
}

func main() {
    var result: Int64 = 0
    var n: Int64 = 2
    while n < 200000 {
        if is_prime(n) != 0 { result += 1 }
        n += 1
    }
    print(result)
}

main()
