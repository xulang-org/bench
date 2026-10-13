package main

import "fmt"

func main() {
	s := 0
	i := 0
	for i < 8000 {
		j := 0
		for j < 8000 {
			s += (i * j) & 1023
			j += 1
		}
		i += 1
	}
	fmt.Println(s)
}
