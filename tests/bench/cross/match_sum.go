package main

import "fmt"

func main() {
	s := 0
	i := 0
	for i < 24000000 {
		switch i & 7 {
		case 0:
			s += 1
		case 1:
			s += 3
		case 2:
			s += 5
		case 3:
			s += 7
		case 4:
			s += 11
		case 5:
			s += 13
		case 6:
			s += 17
		default:
			s += 19
		}
		i += 1
	}
	fmt.Println(s)
	fmt.Println(i)
}
