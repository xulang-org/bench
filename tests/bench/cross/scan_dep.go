package main

import "fmt"

func main() {
	n := 4096
	a := make([]int, n)
	i := 0
	for i < n {
		a[i] = i & 1023
		i += 1
	}
	t := 0
	for t < 20000 {
		i = 1
		for i < n {
			a[i] = a[i] + (a[i-1] & 1023)
			i += 1
		}
		t += 1
	}
	fmt.Println(a[n-1])
}
