// Osprey (MIT): benchmarks/cases/isqrt; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Integer Newton iteration, sum floor(sqrt(i)) over 1..1000000.

func root(n int64) int64 {
	if n < 2 {
		return n
	}
	var x int64 = n
	var y int64 = (x + n/x) / 2
	for y < x {
		x = y
		y = (x + n/x) / 2
	}
	return x
}

func main() {
	var result int64 = 0
	var i int64 = 1
	for i <= 1000000 {
		result += root(i)
		i += 1
	}
	fmt.Println(result)
}
