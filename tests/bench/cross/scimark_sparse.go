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
	const n = 10000
	const nz = 50000
	const nr = 5
	rng := newRandom(101010)
	x := make([]float64, n)
	y := make([]float64, n)
	val := make([]float64, nz)
	col := make([]int, nz)
	row := make([]int, n+1)

	for i := 0; i < n; i++ {
		x[i] = rng.nextDouble()
	}
	for i := 0; i < nz; i++ {
		val[i] = rng.nextDouble()
	}
	for r := 0; r < n; r++ {
		rowR := row[r]
		row[r+1] = rowR + nr
		step := r / nr
		if step < 1 {
			step = 1
		}
		for j := 0; j < nr; j++ {
			col[rowR+j] = (j * step) % n
		}
	}

	acc := 0.0
	for rep := 0; rep < 500; rep++ {
		for r := 0; r < n; r++ {
			s := 0.0
			end := row[r+1]
			for ii := row[r]; ii < end; ii++ {
				s += x[col[ii]] * val[ii]
			}
			y[r] = s
		}
		acc += y[rep%n]
	}

	total := acc
	for i := 0; i < n; i++ {
		total += y[i]
	}
	fmt.Println(int64(math.Floor(total*1000.0 + 0.5)))
}
