// Osprey (MIT): benchmarks/cases/textstats; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.

func hashAt(_ seed: Int64, _ i: Int64) -> Int64 {
    return (((seed + i) * 16807) % 2147483647 * 16807) % 2147483647
}

func word(_ k: Int64) -> String {
    if k == 0 { return "the" }
    if k == 1 { return "quick" }
    if k == 2 { return "brown" }
    if k == 3 { return "fox" }
    if k == 4 { return "jumps" }
    if k == 5 { return "over" }
    if k == 6 { return "lazy" }
    return "dog"
}

func score(_ w: String) -> Int64 {
    var result = Int64(w.utf8.count)
    if w.contains("o") { result += 7 }
    if w.hasPrefix("t") { result += 3 }
    return result
}

func main() {
    var result: Int64 = 0
    var i: Int64 = 0
    while i < 200000 {
        result += score(word(hashAt(1, i) % 8))
        i += 1
    }
    print(result)
}

main()
