package main

import "fmt"

func main() {
	a := make([]int, 0)
	i := 0
	for i < 2000000 {
		a = append(a, i)
		i += 1
	}
	s := 0
	j := 0
	for j < len(a) {
		s += a[j] & 7
		j += 1
	}
	fmt.Println(s)
}
