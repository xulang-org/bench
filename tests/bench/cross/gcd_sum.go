// Osprey (MIT): benchmarks/cases/gcdsum; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Recursive Euclidean GCD: sum gcd(i,1234567), 1 <= i < 2000000.

func gcd(a int64, b int64) int64 {
	if b == 0 {
		return a
	}
	return gcd(b, a%b)
}

func main() {
	var result int64 = 0
	var i int64 = 1
	for i < 2000000 {
		result += gcd(i, 1234567)
		i += 1
	}
	fmt.Println(result)
}
