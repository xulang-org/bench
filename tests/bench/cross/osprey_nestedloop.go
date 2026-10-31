// Osprey (MIT): benchmarks/cases/nestedloop; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Osprey nestedloop: descending 250^3 modular multiply/adds.

func loop_k(i int64, j int64, n int64, initial int64) int64 {
	var k int64 = n
	var acc int64 = initial
	for k != 0 {
		acc = (acc + i*j*k) % 1000000007
		k -= 1
	}
	return acc
}
func loop_j(i int64, n int64, initial int64) int64 {
	var j int64 = n
	var acc int64 = initial
	for j != 0 {
		acc = loop_k(i, j, n, acc)
		j -= 1
	}
	return acc
}
func loop_i(n int64) int64 {
	var i int64 = n
	var acc int64 = 0
	for i != 0 {
		acc = loop_j(i, n, acc)
		i -= 1
	}
	return acc
}

func main() {
	var result int64 = loop_i(250)
	fmt.Println(result)
}
