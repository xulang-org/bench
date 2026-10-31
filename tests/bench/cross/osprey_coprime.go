// Osprey (MIT): benchmarks/cases/coprime; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Osprey coprime: 2000x2000 grid, recursive Euclidean GCD.

func gcd(a int64, b int64) int64 {
	if b == 0 {
		return a
	}
	return gcd(b, a%b)
}

func main() {
	var result int64 = 0
	var i int64 = 2000
	for i > 0 {
		var j int64 = 2000
		for j > 0 {
			if gcd(i, j) == 1 {
				result += 1
			}
			j -= 1
		}
		i -= 1
	}
	fmt.Println(result)
}
