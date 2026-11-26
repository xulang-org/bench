package main

import (
	"fmt"
	"math"
)

type SciRandom struct {
	m    [17]int64
	idxI int
	idxJ int
}

func newRandom(seed int64) SciRandom {
	const m1 int64 = 2147483647
	const m2 int64 = 65536
	var r SciRandom
	jseed := seed
	if jseed < 0 {
		jseed = -jseed
	}
	if jseed > m1 {
		jseed = m1
	}
	if jseed%2 == 0 {
		jseed--
	}
	const k0 int64 = 9069 % m2
	const k1 int64 = 9069 / m2
	j0 := jseed % m2
	j1 := jseed / m2
	for iloop := 0; iloop < 17; iloop++ {
		jseed = j0 * k0
		j1 = (jseed/m2 + j0*k1 + j1*k0) % (m2 / 2)
		j0 = jseed % m2
		r.m[iloop] = j0 + m2*j1
	}
	r.idxI = 4
	r.idxJ = 16
	return r
}

func (r *SciRandom) nextDouble() float64 {
	const m1 int64 = 2147483647
	const dm1 float64 = 1.0 / 2147483647.0
	k := r.m[r.idxI] - r.m[r.idxJ]
	if k < 0 {
		k += m1
	}
	r.m[r.idxJ] = k
	if r.idxI == 0 {
		r.idxI = 16
	} else {
		r.idxI--
	}
	if r.idxJ == 0 {
		r.idxJ = 16
	} else {
		r.idxJ--
	}
	return dm1 * float64(k)
}

func main() {
	const n = 100
	rng := newRandom(101010)
	g := make([]float64, n*n)
	for i := 0; i < n*n; i++ {
		g[i] = rng.nextDouble()
	}

	const omega = 1.25
	const omegaOverFour = omega * 0.25
	const oneMinusOmega = 1.0 - omega
	for p := 0; p < 500; p++ {
		for i := 1; i < n-1; i++ {
			row := i * n
			up := (i - 1) * n
			dn := (i + 1) * n
			for j := 1; j < n-1; j++ {
				g[row+j] = omegaOverFour*(g[up+j]+g[dn+j]+g[row+j-1]+g[row+j+1]) + oneMinusOmega*g[row+j]
			}
		}
	}

	total := 0.0
	for i := 0; i < n*n; i++ {
		total += g[i]
	}
	fmt.Println(int64(math.Floor(total*1000.0 + 0.5)))
}
