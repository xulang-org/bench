// Osprey (MIT): benchmarks/cases/wordfreq; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
// String-keyed frequency map, 200000 tokens, deterministic seed=1.
// Every token performs a map lookup followed by an update (not an indexed counter).
// Eight immutable ASCII keys; weighted final counts; see tests/bench/osprey/README.md.

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

func main() {
    var counts: [String: Int64] = [:]
    var i: Int64 = 0
    while i < 200000 {
        let w = word(hashAt(1, i) % 8)
        let count = counts[w] ?? 0
        counts[w] = count + 1
        i += 1
    }
    var result: Int64 = 0
    i = 0
    while i < 8 {
        result += (i + 1) * (counts[word(i)] ?? 0)
        i += 1
    }
    print(result)
}

main()
