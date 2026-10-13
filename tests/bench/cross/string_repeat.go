package main

import (
	"fmt"
	"strings"
)

func main() {
	seed := "alpha,beta,gamma,delta;omega,phi,chi;lambda,mu,nu"
	total := int64(0)
	for i := 0; i < 25000; i++ {
		out := strings.Repeat(seed, 384+(i&1))
		total += int64(len(out)) + int64(out[100])
	}
	fmt.Println(total)
}
