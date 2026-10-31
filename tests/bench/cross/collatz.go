// Osprey (MIT): benchmarks/cases/collatz; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Recursive Collatz stopping times, summed over 1..100000.

func steps(n int64) int64 {
	if n == 1 {
		return 0
	}
	if n%2 == 0 {
		return 1 + steps(n/2)
	}
	return 1 + steps(3*n+1)
}

func main() {
	var result int64 = 0
	var i int64 = 1
	for i <= 100000 {
		result += steps(i)
		i += 1
	}
	fmt.Println(result)
}
