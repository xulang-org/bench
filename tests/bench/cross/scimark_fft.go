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

func fftBitreverse(data []float64, n int) {
	j := 0
	for i := 0; i < n-1; i++ {
		if i < j {
			ii := 2 * i
			jj := 2 * j
			data[ii], data[jj] = data[jj], data[ii]
			data[ii+1], data[jj+1] = data[jj+1], data[ii+1]
		}
		k := n >> 1
		for k <= j {
			j -= k
			k >>= 1
		}
		j += k
	}
}

func fftTransform(data []float64, n int, direction float64) {
	fftBitreverse(data, n)
	dual := 1
	for bit := 0; bit < 10; bit++ {
		wReal := 1.0
		wImag := 0.0
		theta := 2.0 * direction * math.Pi / (2.0 * float64(dual))
		s := math.Sin(theta)
		t := math.Sin(theta * 0.5)
		s2 := 2.0 * t * t

		for b := 0; b < n; b += 2 * dual {
			i := 2 * b
			j := 2 * (b + dual)
			wdReal := data[j]
			wdImag := data[j+1]
			data[j] = data[i] - wdReal
			data[j+1] = data[i+1] - wdImag
			data[i] += wdReal
			data[i+1] += wdImag
		}

		for a := 1; a < dual; a++ {
			tmpReal := wReal - s*wImag - s2*wReal
			tmpImag := wImag + s*wReal - s2*wImag
			wReal = tmpReal
			wImag = tmpImag
			for b := 0; b < n; b += 2 * dual {
				i := 2 * (b + a)
				j := 2 * (b + a + dual)
				z1Real := data[j]
				z1Imag := data[j+1]
				wdReal := wReal*z1Real - wImag*z1Imag
				wdImag := wReal*z1Imag + wImag*z1Real
				data[j] = data[i] - wdReal
				data[j+1] = data[i+1] - wdImag
				data[i] += wdReal
				data[i+1] += wdImag
			}
		}
		dual *= 2
	}
}

func main() {
	const n = 1024
	rng := newRandom(101010)
	orig := make([]float64, 2*n)
	data := make([]float64, 2*n)
	for i := 0; i < 2*n; i++ {
		orig[i] = rng.nextDouble()
	}

	norm := 1.0 / float64(n)
	acc := 0.0
	for rep := 0; rep < 200; rep++ {
		copy(data, orig)
		fftTransform(data, n, -1.0)
		acc += math.Abs(data[0]) + math.Abs(data[1]) + math.Abs(data[2*((rep*7)%512)])
		fftTransform(data, n, 1.0)
		for i := 0; i < 2*n; i++ {
			data[i] *= norm
		}
		acc += math.Abs(data[2*((rep*13)%512)])
	}
	fmt.Println(int64(math.Floor(acc*10.0 + 0.5)))
}
