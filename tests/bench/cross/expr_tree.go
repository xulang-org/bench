// Osprey (MIT): benchmarks/cases/exprtree; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
package main

import "fmt"

type Expr struct {
	tag, value  int64
	left, right *Expr
}

func hashAt(seed, idx int64) int64 {
	return (((seed + idx) * 16807) % 2147483647 * 16807) % 2147483647
}

func build(seed, idx, depth int64) *Expr {
	if depth == 0 {
		return &Expr{tag: 0, value: hashAt(seed, idx) % 1000}
	}
	left := build(seed, idx*2+1, depth-1)
	right := build(seed, idx*2+2, depth-1)
	return &Expr{tag: 1 + hashAt(seed, idx)%2, left: left, right: right}
}

func eval(e *Expr) int64 {
	if e.tag == 0 {
		return e.value
	}
	left := eval(e.left)
	right := eval(e.right)
	if e.tag == 1 {
		return (left + right) % 1000000007
	}
	return (left * right) % 1000000007
}

func main() {
	var total int64 = 0
	var t int64 = 0
	for t < 10 {
		expr := build(1+t*7, 1, 14)
		total = (total + eval(expr)) % 1000000007
		t += 1
	}
	fmt.Println(total)
}
