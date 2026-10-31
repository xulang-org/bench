// Osprey (MIT): benchmarks/cases/ackermann; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Ackermann(3,10): nested, data-dependent recursion.

func add(_ a: Int64, _ b: Int64) -> Int64 { return a + b }
func sub(_ a: Int64, _ b: Int64) -> Int64 { return a - b }
func ack(_ m: Int64, _ n: Int64) -> Int64 {
    if m == 0 { return add(n, 1) }
    if n == 0 { return ack(sub(m, 1), 1) }
    return ack(sub(m, 1), ack(m, sub(n, 1)))
}

func main() {
    var result: Int64 = ack(3, 10)
    print(result)
}

main()
