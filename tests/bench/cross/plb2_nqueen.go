package main

import "fmt"

func nqSolve(n int) int64 {
	var l, c, r, m [32]int64
	y0 := (int64(1) << n) - 1
	k := 0
	m[0] = y0
	var cnt int64 = 0
	for k >= 0 {
		y := m[k]
		if y == 0 {
			k -= 1
		} else {
			z := y & -y
			m[k] = y - z
			if k == n-1 {
				cnt += 1
			} else {
				k += 1
				l[k] = ((l[k-1] | z) << 1) & y0
				c[k] = c[k-1] | z
				r[k] = (r[k-1] | z) >> 1
				m[k] = y0 ^ (l[k] | c[k] | r[k])
			}
		}
	}
	return cnt
}

func main() {
	fmt.Println(nqSolve(15))
}
