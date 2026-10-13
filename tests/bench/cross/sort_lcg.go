package main

import (
	"fmt"
	"sort"
)

func main() {
	a := make([]int, 0)
	i := 0
	x := 12345
	for i < 100000 {
		x = (x*1103515245 + 12345) & 0x7FFFFFFF
		a = append(a, x)
		i += 1
	}
	sort.Ints(a)
	fmt.Println(a[0] + a[50000]*2 + a[99999]*3)
}
