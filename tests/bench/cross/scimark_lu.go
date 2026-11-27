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
	a0 := make([]float64, n*n)
	a := make([]float64, n*n)
	piv := make([]int64, n)
	for i := 0; i < n*n; i++ {
		a0[i] = rng.nextDouble()
	}

	luAcc := 0.0
	var pivChk int64 = 0
	for rep := 0; rep < 30; rep++ {
		copy(a, a0)
		for j := 0; j < n; j++ {
			jp := j
			t := math.Abs(a[j*n+j])
			for i := j + 1; i < n; i++ {
				ab := math.Abs(a[i*n+j])
				if ab > t {
					jp = i
					t = ab
				}
			}
			piv[j] = int64(jp)
			if jp != j {
				for k := 0; k < n; k++ {
					a[j*n+k], a[jp*n+k] = a[jp*n+k], a[j*n+k]
				}
			}
			if j < n-1 {
				recp := 1.0 / a[j*n+j]
				for k := j + 1; k < n; k++ {
					a[k*n+j] *= recp
				}
				for ii := j + 1; ii < n; ii++ {
					aii := a[ii*n+j]
					for jj := j + 1; jj < n; jj++ {
						a[ii*n+jj] -= aii * a[j*n+jj]
					}
				}
			}
		}
		for i := 0; i < n*n; i++ {
			luAcc += math.Abs(a[i])
		}
		var ps int64 = 0
		for i := 0; i < n; i++ {
			ps += piv[i]
		}
		pivChk = (pivChk + ps) % 1000000007
	}
	fmt.Println(int64(math.Floor(luAcc*100.0+0.5)) + pivChk)
}
