package main

import "fmt"

type Acc struct {
	n int
}

func (a *Acc) add(x int) {
	a.n += x
}

func main() {
	a := Acc{n: 0}
	i := 0
	for i < 8000000 {
		a.add(i & 7)
		i += 1
	}
	fmt.Println(a.n)
}
