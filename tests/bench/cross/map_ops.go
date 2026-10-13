package main

import "fmt"

func main() {
	m := map[int]int{}
	i := 0
	for i < 200000 {
		m[i] = 1
		i += 1
	}
	s := 0
	i = 0
	for i < 200000 {
		s += m[i] + i
		i += 1
	}
	fmt.Println(s)
}
