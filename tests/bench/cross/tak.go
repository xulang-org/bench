// Osprey (MIT): benchmarks/cases/tak; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Takeuchi tak(32,16,8): ternary recursion with recursive arguments.

func sub(a int64, b int64) int64 { return a - b }
func tak(x int64, y int64, z int64) int64 {
	if x > y {
		return tak(tak(sub(x, 1), y, z), tak(sub(y, 1), z, x), tak(sub(z, 1), x, y))
	}
	return z
}

func main() {
	var result int64 = tak(32, 16, 8)
	fmt.Println(result)
}
