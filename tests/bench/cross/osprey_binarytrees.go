// Osprey (MIT): benchmarks/cases/binarytrees; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

type Tree struct{ left, right *Tree }

func makeTree(depth int64) *Tree {
	if depth == 0 {
		return &Tree{}
	}
	left := makeTree(depth - 1)
	right := makeTree(depth - 1)
	return &Tree{left, right}
}

func check(t *Tree) int64 {
	if t == nil {
		return 0
	}
	return 1 + check(t.left) + check(t.right)
}

func main() {
	var result int64 = 0
	var i int64 = 0
	for i < 1200 {
		tree := makeTree(13)
		result += check(tree)
		i += 1
	}
	fmt.Println(result)
}
