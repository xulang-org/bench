package main

import "fmt"

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
	rng := newRandom(113)
	var under int64 = 0
	for i := 0; i < 5000000; i++ {
		x := rng.nextDouble()
		y := rng.nextDouble()
		if x*x+y*y <= 1.0 {
			under++
		}
	}
	fmt.Println(under)
}
