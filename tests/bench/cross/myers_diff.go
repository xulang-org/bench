package main

import "fmt"

const modV int64 = 1000000007

func main() {
	const maxD = 120
	const stride = 241
	const off = 120

	v := make([]int, stride)
	trace := make([]int, (maxD+1)*stride)
	a := make([]int64, 200)
	b := make([]int64, 300)
	opType := make([]int64, 600)
	opVal := make([]int64, 600)

	var rng int64 = 20260501
	var totalEdits int64
	var ck int64

	for pair := 0; pair < 1200; pair++ {
		n := 200
		for i := 0; i < n; i++ {
			rng = (rng*1103515245 + 12345) & 2147483647
			val := rng & 63
			a[i] = val
			b[i] = val
		}
		m := n
		rng = (rng*1103515245 + 12345) & 2147483647
		nmut := int(18 + (rng % 11))
		for mi := 0; mi < nmut; mi++ {
			rng = (rng*1103515245 + 12345) & 2147483647
			kind := rng % 3
			if kind == 0 && m > 120 {
				rng = (rng*1103515245 + 12345) & 2147483647
				pos := int(rng % int64(m))
				for p := pos; p+1 < m; p++ {
					b[p] = b[p+1]
				}
				m--
			} else if kind == 1 && m < 260 {
				rng = (rng*1103515245 + 12345) & 2147483647
				pos := int(rng % int64(m+1))
				rng = (rng*1103515245 + 12345) & 2147483647
				nv := rng & 63
				for p := m; p > pos; p-- {
					b[p] = b[p-1]
				}
				b[pos] = nv
				m++
			} else {
				rng = (rng*1103515245 + 12345) & 2147483647
				pos := int(rng % int64(m))
				rng = (rng*1103515245 + 12345) & 2147483647
				b[pos] = rng & 63
			}
		}

		v[off+1] = 0
		foundD := -1
		for d := 0; d <= maxD; d++ {
			tbase := d * stride
			for k := -d; k <= d; k += 2 {
				var x int
				if k == -d || (k != d && v[off+k-1] < v[off+k+1]) {
					x = v[off+k+1]
				} else {
					x = v[off+k-1] + 1
				}
				y := x - k
				for x < n && y < m && a[x] == b[y] {
					x++
					y++
				}
				v[off+k] = x
				trace[tbase+off+k] = x
				if x >= n && y >= m {
					foundD = d
					break
				}
			}
			if foundD >= 0 {
				break
			}
		}

		x := n
		y := m
		oc := 0
		for bd := foundD; bd > 0; bd-- {
			pbase := (bd - 1) * stride
			k := x - y
			var prevK int
			if k == -bd || (k != bd && trace[pbase+off+k-1] < trace[pbase+off+k+1]) {
				prevK = k + 1
			} else {
				prevK = k - 1
			}
			prevX := trace[pbase+off+prevK]
			prevY := prevX - prevK
			for x > prevX && y > prevY {
				opType[oc] = 0
				opVal[oc] = a[x-1]
				oc++
				x--
				y--
			}
			if x == prevX {
				opType[oc] = 1
				opVal[oc] = b[y-1]
				oc++
				y--
			} else {
				opType[oc] = 2
				opVal[oc] = a[x-1]
				oc++
				x--
			}
		}
		for x > 0 && y > 0 {
			opType[oc] = 0
			opVal[oc] = a[x-1]
			oc++
			x--
			y--
		}

		totalEdits += int64(foundD)
		sh := int64(foundD)
		for j := 0; j < oc; j++ {
			sh = (sh*131 + opType[j]*67 + opVal[j]) % modV
		}
		ck = (ck*31 + sh) % modV
	}

	fmt.Printf("%d\n%d\n", totalEdits, ck)
}
