// Osprey (MIT): benchmarks/cases/fib; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Osprey fib: naive fib(35), including the original two base cases.

func add(a int64, b int64) int64 { return a + b }
func sub(a int64, b int64) int64 { return a - b }
func fib(n int64) int64 {
	if n == 0 {
		return 0
	}
	if n == 1 {
		return 1
	}
	return add(fib(sub(n, 1)), fib(sub(n, 2)))
}

func main() {
	var result int64 = fib(35)
	fmt.Println(result)
}
