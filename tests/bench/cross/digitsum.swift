// Osprey (MIT): benchmarks/cases/digitsum; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Recursive decimal digit sums, summed over 1..2000000.

func digit_sum(_ n: Int64) -> Int64 {
    if n < 10 { return n }
    return n % 10 + digit_sum(n / 10)
}

func main() {
    var result: Int64 = 0
    var i: Int64 = 1
    while i <= 2000000 {
        result += digit_sum(i)
        i += 1
    }
    print(result)
}

main()
