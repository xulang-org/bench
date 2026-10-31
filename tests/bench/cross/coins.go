// Osprey (MIT): benchmarks/cases/coins; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Unmemoised SICP change counting: amount 600, denominations 1/5/10/25/50.

func coin(k int64) int64 {
	if k == 1 {
		return 1
	}
	if k == 2 {
		return 5
	}
	if k == 3 {
		return 10
	}
	if k == 4 {
		return 25
	}
	return 50
}
func ways(amount int64, kind int64) int64 {
	if amount == 0 {
		return 1
	}
	if amount < 0 {
		return 0
	}
	if kind == 0 {
		return 0
	}
	return ways(amount-coin(kind), kind) + ways(amount, kind-1)
}

func main() {
	var result int64 = ways(600, 5)
	fmt.Println(result)
}
