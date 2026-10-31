// Osprey (MIT): benchmarks/cases/textstats; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import (
	"fmt"
	"strings"
)

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

func score(w string) int64 {
	result := int64(len(w))
	if strings.Contains(w, "o") {
		result += 7
	}
	if strings.HasPrefix(w, "t") {
		result += 3
	}
	return result
}

func main() {
	var result int64 = 0
	var i int64 = 0
	for i < 200000 {
		result += score(word(hashAt(1, i) % 8))
		i += 1
	}
	fmt.Println(result)
}
