package main

import (
	"fmt"
	"strings"
)

func main() {
	seed := "alpha,beta,gamma,delta;omega,phi,chi;lambda,mu,nu"
	base := strings.Repeat(seed, 384)
	total := int64(0)
	i := 0
	for i < 2500 {
		s := strings.ReplaceAll(base, "a", "A")
		total += int64(len(s))
		parts := strings.Split(s, ";")
		total += int64(len(parts))
		j := 0
		for j < len(parts) {
			p := parts[j]
			total += int64(len(p))
			if strings.HasPrefix(p, "A") {
				total += 1
			}
			total += int64(strings.Count(p, "a"))
			j += 1
		}
		line := strings.Join(parts, "|")
		total += int64(len(line))

		trimmed := strings.TrimSpace(line)
		r := strings.NewReader(trimmed)
		buf := make([]byte, 256)
		n, _ := r.Read(buf)
		total += int64(n)
		rem := r.Len()
		if rem > 0 {
			total += int64(rem)
		}
		i += 1
	}
	fmt.Printf("%d\n", total)
}
