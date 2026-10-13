package main

import "fmt"

func main() {
	s := 0.0
	i := 0
	for i < 20000000 {
		s += float64(i & 1023)
		i += 1
	}
	fmt.Println(int(s))
}
