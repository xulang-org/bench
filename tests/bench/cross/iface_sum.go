package main

import "fmt"

type Src interface {
	val() int
}

type A struct{ x int }
type B struct{ x int }

func (a A) val() int { return a.x }
func (b B) val() int { return b.x * 2 }

func main() {
	xs := []Src{A{x: 1}, B{x: 2}}
	s := 0
	i := 0
	for i < 8000000 {
		s += xs[i&1].val()
		i += 1
	}
	fmt.Println(s)
}
