// Osprey (MIT): benchmarks/cases/mergesort; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

// Top-down merge sort with alternating split and fresh growable vectors.
// 8 rounds x 2000 values; seed=1+131*t, rank-weighted modular checksum.
// Identical split/merge/push loops in all ports; see tests/bench/osprey/README.md.

func hashAt(seed, i int64) int64 {
	return (((seed + i) * 16807) % 2147483647 * 16807) % 2147483647
}

func merge(left, right []int64) []int64 {
	result := []int64{}
	var i, j int64 = 0, 0
	for i < int64(len(left)) && j < int64(len(right)) {
		if right[j] < left[i] {
			result = append(result, right[j])
			j += 1
		} else {
			result = append(result, left[i])
			i += 1
		}
	}
	for i < int64(len(left)) {
		result = append(result, left[i])
		i += 1
	}
	for j < int64(len(right)) {
		result = append(result, right[j])
		j += 1
	}
	return result
}

func mergeSort(xs []int64) []int64 {
	if len(xs) < 2 {
		result := []int64{}
		var i int64 = 0
		for i < int64(len(xs)) {
			result = append(result, xs[i])
			i += 1
		}
		return result
	}
	evens := []int64{}
	odds := []int64{}
	var i int64 = 0
	for i < int64(len(xs)) {
		evens = append(evens, xs[i])
		i += 2
	}
	i = 1
	for i < int64(len(xs)) {
		odds = append(odds, xs[i])
		i += 2
	}
	left := mergeSort(evens)
	right := mergeSort(odds)
	return merge(left, right)
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
		sorted := mergeSort(xs)
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
