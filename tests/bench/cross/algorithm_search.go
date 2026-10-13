package main

import (
	"fmt"
	"sort"
)

func main() {
	n := 131072
	a := make([]int, n)
	for i := 0; i < n; i++ {
		a[i] = i * 3
	}
	total := int64(0)
	for q := int64(0); q < 4000000; q++ {
		v := int(((q * 1103515245 + 12345) & 0x3FFFF) * 3)
		total += int64(sort.SearchInts(a, v))
	}
	fmt.Printf("%d\n", total)
}
