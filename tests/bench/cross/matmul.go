package main

import "fmt"

func main() {
	n := 250
	nn := n * n
	a := make([]int, nn)
	b := make([]int, nn)
	c := make([]int, nn)
	i := 0
	for i < n {
		j := 0
		for j < n {
			a[i*n+j] = (i*31 + j*7) & 1023
			b[i*n+j] = (i*17 + j*13) & 1023
			j += 1
		}
		i += 1
	}
	i = 0
	for i < n {
		k := 0
		for k < n {
			aik := a[i*n+k]
			j := 0
			for j < n {
				c[i*n+j] = c[i*n+j] + aik*b[k*n+j]
				j += 1
			}
			k += 1
		}
		i += 1
	}
	s := 0
	t := 0
	for t < nn {
		s += c[t]
		t += 1
	}
	fmt.Println(s)
}
