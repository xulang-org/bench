// Osprey (MIT): benchmarks/cases/listops; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

func hashAt(seed, i int64) int64 {
	return (((seed + i) * 16807) % 2147483647 * 16807) % 2147483647
}

func sumList(xs []int64, i int64) int64 {
	if i == int64(len(xs)) {
		return 0
	}
	return xs[i] + sumList(xs, i+1)
}

func belowList(xs []int64, i int64) int64 {
	if i == int64(len(xs)) {
		return 0
	}
	var add int64 = 0
	if xs[i] < 500 {
		add = 1
	}
	return add + belowList(xs, i+1)
}

func main() {
	var total int64 = 0
	var t int64 = 0
	for t < 8 {
		xs := []int64{}
		var i int64 = 0
		for i < 4000 {
			xs = append(xs, hashAt(1+t*131, i)%1000)
			i += 1
		}
		total = (total + sumList(xs, 0) + belowList(xs, 0)) % 1000000007
		t += 1
	}
	fmt.Println(total)
}
