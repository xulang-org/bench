// Osprey (MIT): benchmarks/cases/hanoi; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Accumulator-threaded double recursion for 25 Hanoi disks; count moves.

func moves(n int64, acc int64) int64 {
	if n == 0 {
		return acc
	}
	return moves(n-1, moves(n-1, acc)+1)
}

func main() {
	var result int64 = moves(25, 0)
	fmt.Println(result)
}
