// Osprey (MIT): benchmarks/cases/josephus; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Josephus survivor, zero-based, n=10000000 and k=7; variable divisor chain.

func main() {
	var result int64 = 0
	var i int64 = 2
	for i <= 10000000 {
		result = (result + 7) % i
		i += 1
	}
	fmt.Println(result)
}
