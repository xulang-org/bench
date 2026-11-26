package main

import "fmt"

func lcg(seed int64) int64 {
	return (seed*1103515245 + 12345) & 2147483647
}

func main() {
	const n = 200000
	const q = 200000
	st := make([]int64, n)
	en := make([]int64, n)
	maxEn := make([]int64, n)

	var seed int64 = 123456789
	var curSt int64 = 0
	for i := 0; i < n; i++ {
		seed = lcg(seed)
		curSt += seed % 100
		seed = lcg(seed)
		ln := 1 + (seed % 5000)
		st[i] = curSt
		en[i] = curSt + ln
	}
	maxCoord := curSt + 1

	qst := make([]int64, q)
	qen := make([]int64, q)
	for i := 0; i < q; i++ {
		seed = lcg(seed)
		qs := seed % maxCoord
		seed = lcg(seed)
		ln := 1 + (seed % 5000)
		qst[i] = qs
		qen[i] = qs + ln
	}

	for i := 0; i < n; i += 2 {
		maxEn[i] = en[i]
	}
	k := 1
	for (1 << k) <= n {
		x := 1 << (k - 1)
		i0 := (x << 1) - 1
		step := x << 2
		for i := i0; i < n; i += step {
			el := maxEn[i-x]
			var er int64
			if i+x < n {
				er = maxEn[i+x]
			} else {
				er = en[i]
				lim := i + (x << 1)
				if lim > n {
					lim = n
				}
				for j := i + 1; j < lim; j++ {
					if en[j] > er {
						er = en[j]
					}
				}
			}
			e := en[i]
			if el > e {
				e = el
			}
			if er > e {
				e = er
			}
			maxEn[i] = e
		}
		k++
	}
	maxK := k - 1

	var sk, sx, sw [64]int
	var hits int64 = 0
	var covSum int64 = 0
	rootX := (1 << maxK) - 1

	for qi := 0; qi < q; qi++ {
		qs := qst[qi]
		qe := qen[qi]
		sk[0] = maxK
		sx[0] = rootX
		sw[0] = 0
		sp := 1
		for sp > 0 {
			sp--
			kk := sk[sp]
			x := sx[sp]
			w := sw[sp]
			if kk <= 3 {
				i0 := (x >> kk) << kk
				i1 := i0 + (1 << (kk + 1)) - 1
				if i1 >= n {
					i1 = n
				}
				for ii := i0; ii < i1 && st[ii] < qe; ii++ {
					if qs < en[ii] {
						hits++
						os := st[ii]
						if qs > os {
							os = qs
						}
						oe := en[ii]
						if qe < oe {
							oe = qe
						}
						covSum += oe - os
					}
				}
			} else if w == 0 {
				y := x - (1 << (kk - 1))
				sk[sp] = kk
				sx[sp] = x
				sw[sp] = 1
				sp++
				if y >= n || maxEn[y] > qs {
					sk[sp] = kk - 1
					sx[sp] = y
					sw[sp] = 0
					sp++
				}
			} else if x < n && st[x] < qe {
				if qs < en[x] {
					hits++
					os := st[x]
					if qs > os {
						os = qs
					}
					oe := en[x]
					if qe < oe {
						oe = qe
					}
					covSum += oe - os
				}
				sk[sp] = kk - 1
				sx[sp] = x + (1 << (kk - 1))
				sw[sp] = 0
				sp++
			}
		}
	}
	fmt.Println(hits)
	fmt.Println(covSum)
}
