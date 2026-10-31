// Osprey (MIT): benchmarks/cases/digitsum; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Recursive decimal digit sums, summed over 1..2000000.

func digit_sum(n int64) int64 {
	if n < 10 {
		return n
	}
	return n%10 + digit_sum(n/10)
}

func main() {
	var result int64 = 0
	var i int64 = 1
	for i <= 2000000 {
		result += digit_sum(i)
		i += 1
	}
	fmt.Println(result)
}
