// Osprey (MIT): benchmarks/cases/wordfreq; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// String-keyed frequency map, 200000 tokens, deterministic seed=1.
// Every token performs a map lookup followed by an update (not an indexed counter).
// Eight immutable ASCII keys; weighted final counts; see tests/bench/osprey/README.md.

func hashAt(seed, i int64) int64 {
	return (((seed + i) * 16807) % 2147483647 * 16807) % 2147483647
}

func word(k int64) string {
	if k == 0 {
		return "the"
	}
	if k == 1 {
		return "quick"
	}
	if k == 2 {
		return "brown"
	}
	if k == 3 {
		return "fox"
	}
	if k == 4 {
		return "jumps"
	}
	if k == 5 {
		return "over"
	}
	if k == 6 {
		return "lazy"
	}
	return "dog"
}

func main() {
	counts := map[string]int64{}
	var i int64 = 0
	for i < 200000 {
		w := word(hashAt(1, i) % 8)
		count := counts[w]
		counts[w] = count + 1
		i += 1
	}
	var result int64 = 0
	i = 0
	for i < 8 {
		result += (i + 1) * counts[word(i)]
		i += 1
	}
	fmt.Println(result)
}
