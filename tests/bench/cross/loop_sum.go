package main

import "fmt"

func main() {
	s := 0
	i := 0
	for i < 50000000 {
		s += i & 1023
		i += 1
	}
	fmt.Println(s)
}
