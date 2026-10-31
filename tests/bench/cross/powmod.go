// Osprey (MIT): benchmarks/cases/powmod; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Sum i^20 mod 1000000007, 1 <= i < 1000000; twenty multiplies, no squaring.

func power(base int64, e int64, acc int64) int64 {
	if e == 0 {
		return acc
	}
	return power(base, e-1, (acc*base)%1000000007)
}

func main() {
	var result int64 = 0
	var i int64 = 1
	for i < 1000000 {
		result = (result + power(i, 20, 1)) % 1000000007
		i += 1
	}
	fmt.Println(result)
}
