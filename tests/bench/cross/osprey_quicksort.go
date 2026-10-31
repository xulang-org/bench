// Osprey (MIT): benchmarks/cases/quicksort; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Osprey first-element-pivot quicksort; two partition passes and fresh vectors.
// 8 rounds x 2000 values; seed=1+131*t, rank-weighted modular checksum.
// Identical partition/concatenate/push loops in all ports; see tests/bench/osprey/README.md.

func hashAt(seed, i int64) int64 {
	return (((seed + i) * 16807) % 2147483647 * 16807) % 2147483647
}

func quicksort(xs []int64) []int64 {
	if len(xs) == 0 {
		return []int64{}
	}
	pivot := xs[0]
	below := []int64{}
	atLeast := []int64{}
	var i int64 = 1
	for i < int64(len(xs)) {
		if xs[i] < pivot {
			below = append(below, xs[i])
		}
		i += 1
	}
	i = 1
	for i < int64(len(xs)) {
		if xs[i] >= pivot {
			atLeast = append(atLeast, xs[i])
		}
		i += 1
	}
	sorted := quicksort(below)
	sorted = append(sorted, pivot)
	right := quicksort(atLeast)
	i = 0
	for i < int64(len(right)) {
		sorted = append(sorted, right[i])
		i += 1
	}
	return sorted
}

func main() {
	var total int64 = 0
	var t int64 = 0
	for t < 8 {
		xs := []int64{}
		var i int64 = 0
		for i < 2000 {
			xs = append(xs, hashAt(1+t*131, i)%100000)
			i += 1
		}
		sorted := quicksort(xs)
		var weight int64 = 0
		i = 0
		for i < int64(len(sorted)) {
			weight = (weight + sorted[i]*(i+1)) % 1000000007
			i += 1
		}
		total = (total + weight) % 1000000007
		t += 1
	}
	fmt.Println(total)
}
