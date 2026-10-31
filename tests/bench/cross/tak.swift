// Osprey (MIT): benchmarks/cases/tak; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// Takeuchi tak(32,16,8): ternary recursion with recursive arguments.

func sub(_ a: Int64, _ b: Int64) -> Int64 { return a - b }
func tak(_ x: Int64, _ y: Int64, _ z: Int64) -> Int64 {
    if x > y {
        return tak(tak(sub(x, 1), y, z), tak(sub(y, 1), z, x), tak(sub(z, 1), x, y))
    }
    return z
}

func main() {
    var result: Int64 = tak(32, 16, 8)
    print(result)
}

main()
