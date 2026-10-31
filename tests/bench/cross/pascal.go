// Osprey (MIT): benchmarks/cases/pascal; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Unmemoised Pascal recursion: binomial coefficient C(27,13).

func binom(n int64, k int64) int64 {
	if k == 0 {
		return 1
	}
	if k == n {
		return 1
	}
	return binom(n-1, k-1) + binom(n-1, k)
}

func main() {
	var result int64 = binom(27, 13)
	fmt.Println(result)
}
