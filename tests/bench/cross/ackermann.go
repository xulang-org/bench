// Osprey (MIT): benchmarks/cases/ackermann; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Ackermann(3,10): nested, data-dependent recursion.

func add(a int64, b int64) int64 { return a + b }
func sub(a int64, b int64) int64 { return a - b }
func ack(m int64, n int64) int64 {
	if m == 0 {
		return add(n, 1)
	}
	if n == 0 {
		return ack(sub(m, 1), 1)
	}
	return ack(sub(m, 1), ack(m, sub(n, 1)))
}

func main() {
	var result int64 = ack(3, 10)
	fmt.Println(result)
}
