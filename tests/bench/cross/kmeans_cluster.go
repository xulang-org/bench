package main

import (
	"fmt"
	"math"
)

const modV int64 = 1000000007

func main() {
	const n = 8192
	const d = 8
	const k = 16
	var rng int64 = 84848484

	gt := make([]float64, k*d)
	for c := 0; c < k*d; c++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		gt[c] = float64((rng%1000)-500) / 16.0
	}

	pts := make([]float64, n*d)
	assign := make([]int, n)
	for i := 0; i < n; i++ {
		g := i & 15
		for dim := 0; dim < d; dim++ {
			rng = (rng*1103515245 + 12345) & 2147483647
			pts[i*d+dim] = gt[g*d+dim] + float64((rng%129)-64)/32.0
		}
	}

	cent := make([]float64, k*d)
	sumC := make([]float64, k*d)
	copy(cent, pts[:k*d])
	cnt := make([]int, k)
	finalInertia := 0.0

	for it := 0; it < 25; it++ {
		for c := 0; c < k*d; c++ {
			sumC[c] = 0.0
		}
		for c := 0; c < k; c++ {
			cnt[c] = 0
		}
		inertia := 0.0
		for i := 0; i < n; i++ {
			pb := i * d
			bestC := 0
			bestD := 1.0e18
			for c := 0; c < k; c++ {
				cb := c * d
				dist := 0.0
				for dim := 0; dim < d; dim++ {
					diff := pts[pb+dim] - cent[cb+dim]
					dist += diff * diff
				}
				if dist < bestD {
					bestD = dist
					bestC = c
				}
			}
			assign[i] = bestC
			cnt[bestC]++
			inertia += bestD
			cb := bestC * d
			for dim := 0; dim < d; dim++ {
				sumC[cb+dim] += pts[pb+dim]
			}
		}
		for c := 0; c < k; c++ {
			if cnt[c] > 0 {
				inv := 1.0 / float64(cnt[c])
				cb := c * d
				for dim := 0; dim < d; dim++ {
					cent[cb+dim] = sumC[cb+dim] * inv
				}
			}
		}
		finalInertia = inertia
	}

	var ack int64
	for i := 0; i < n; i++ {
		ack = (ack*31 + int64(assign[i]) + 1) % modV
	}

	fmt.Printf("%d\n%d\n", ack, int64(math.Floor(finalInertia+0.5)))
}
