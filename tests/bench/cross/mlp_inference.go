package main

import (
	"fmt"
	"math"
)

func main() {
	const d0 = 64
	const d1 = 128
	const d2 = 64
	const d3 = 16
	var rng int64 = 73737373

	w1 := make([]float64, d1*d0)
	b1 := make([]float64, d1)
	w2 := make([]float64, d2*d1)
	b2 := make([]float64, d2)
	w3 := make([]float64, d3*d2)
	b3 := make([]float64, d3)

	for k := 0; k < d1*d0; k++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		w1[k] = float64((rng%255)-127) / 1024.0
	}
	for k := 0; k < d1; k++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		b1[k] = float64((rng%63)-31) / 256.0
	}
	for k := 0; k < d2*d1; k++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		w2[k] = float64((rng%255)-127) / 1024.0
	}
	for k := 0; k < d2; k++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		b2[k] = float64((rng%63)-31) / 256.0
	}
	for k := 0; k < d3*d2; k++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		w3[k] = float64((rng%255)-127) / 1024.0
	}
	for k := 0; k < d3; k++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		b3[k] = float64((rng%63)-31) / 256.0
	}

	x := make([]float64, d0)
	h1 := make([]float64, d1)
	h2 := make([]float64, d2)
	var clsSum int64
	logitAcc := 0.0

	for smp := 0; smp < 2000; smp++ {
		for i := 0; i < d0; i++ {
			rng = (rng*1103515245 + 12345) & 2147483647
			x[i] = float64((rng%255)-127) / 128.0
		}
		for j := 0; j < d1; j++ {
			s := b1[j]
			base := j * d0
			for i := 0; i < d0; i++ {
				s += x[i] * w1[base+i]
			}
			if s > 0.0 {
				h1[j] = s
			} else {
				h1[j] = 0.0
			}
		}
		for j := 0; j < d2; j++ {
			s := b2[j]
			base := j * d1
			for i := 0; i < d1; i++ {
				s += h1[i] * w2[base+i]
			}
			if s > 0.0 {
				h2[j] = s
			} else {
				h2[j] = 0.0
			}
		}
		bestC := 0
		bestV := -1.0e18
		for j := 0; j < d3; j++ {
			s := b3[j]
			base := j * d2
			for i := 0; i < d2; i++ {
				s += h2[i] * w3[base+i]
			}
			if s > bestV {
				bestV = s
				bestC = j
			}
		}
		clsSum += int64(bestC)
		logitAcc += math.Abs(bestV)
	}

	fmt.Printf("%d\n%d\n", clsSum, int64(math.Floor(logitAcc*10.0+0.5)))
}
