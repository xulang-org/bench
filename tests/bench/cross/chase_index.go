package main

import "fmt"

func main() {
	n := 65536
	nxt := make([]int, n)
	i := 0
	for i < n {
		nxt[i] = ((i * 7) + 1) & (n - 1)
		i += 1
	}
	k := 0
	s := 0
	for s < 20000000 {
		k = nxt[k]
		s += 1
	}
	fmt.Println(k)
}
