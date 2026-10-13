package main

import "fmt"

func main() {
	n := 1048576
	src := make([]int, n)
	dst := make([]int, n)
	i := 0
	for i < n {
		src[i] = i & 1023
		dst[i] = i & 1023
		i += 1
	}
	t := 0
	for t < 80 {
		i = 0
		for i < n {
			dst[i] = src[i]
			i += 1
		}
		t += 1
	}
	s := 0
	i = 0
	for i < n {
		s += dst[i]
		i += 1
	}
	fmt.Println(s)
}
