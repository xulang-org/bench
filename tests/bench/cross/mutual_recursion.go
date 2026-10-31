// Osprey (MIT): benchmarks/cases/mutual; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Mutually recursive parity, i%1000 for 1 <= i < 130000.

func even(n int64) int64 {
	if n == 0 {
		return 1
	}
	return odd(n - 1)
}
func odd(n int64) int64 {
	if n == 0 {
		return 0
	}
	return even(n - 1)
}

func main() {
	var result int64 = 0
	var i int64 = 1
	for i < 130000 {
		result += even(i % 1000)
		i += 1
	}
	fmt.Println(result)
}
