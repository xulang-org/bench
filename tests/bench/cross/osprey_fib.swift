// Osprey (MIT): benchmarks/cases/fib; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Osprey fib: naive fib(35), including the original two base cases.

func add(_ a: Int64, _ b: Int64) -> Int64 { return a + b }
func sub(_ a: Int64, _ b: Int64) -> Int64 { return a - b }
func fib(_ n: Int64) -> Int64 {
    if n == 0 { return 0 }
    if n == 1 { return 1 }
    return add(fib(sub(n, 1)), fib(sub(n, 2)))
}

func main() {
    var result: Int64 = fib(35)
    print(result)
}

main()
