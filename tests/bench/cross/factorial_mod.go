// Osprey (MIT): benchmarks/cases/factorial; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Product 1..10000000 modulo 1000000007; dependent multiply/remainder fold.

func main() {
	var result int64 = 1
	var i int64 = 1
	for i <= 10000000 {
		result = (result * i) % 1000000007
		i += 1
	}
	fmt.Println(result)
}
