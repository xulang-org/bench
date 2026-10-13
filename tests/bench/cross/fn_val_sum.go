package main

import "fmt"

func bump(x int) int {
	return x + 1
}

func main() {
	f := bump
	s := 0
	i := 0
	for i < 8000000 {
		s += f(i & 7)
		i += 1
	}
	fmt.Println(s)
}
