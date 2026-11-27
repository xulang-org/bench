package main

import "fmt"

const modV int64 = 1000000007

func lessRec(k1, s1, k2, s2 int64) bool {
	if k1 != k2 {
		return k1 < k2
	}
	return s1 > s2
}

func swapRun(rk, rs, rv, rt []int64, a, b int) {
	rk[a], rk[b] = rk[b], rk[a]
	rs[a], rs[b] = rs[b], rs[a]
	rv[a], rv[b] = rv[b], rv[a]
	rt[a], rt[b] = rt[b], rt[a]
}

func siftMaxRun(rk, rs, rv, rt []int64, start, n int) {
	i := start
	for {
		l := i*2 + 1
		if l >= n {
			break
		}
		best := l
		r := l + 1
		if r < n && lessRec(rk[best], rs[best], rk[r], rs[r]) {
			best = r
		}
		if lessRec(rk[i], rs[i], rk[best], rs[best]) {
			swapRun(rk, rs, rv, rt, i, best)
			i = best
		} else {
			break
		}
	}
}

func heapsortRun(rk, rs, rv, rt []int64, n int) {
	for start := n/2 - 1; start >= 0; start-- {
		siftMaxRun(rk, rs, rv, rt, start, n)
	}
	for end := n - 1; end > 0; end-- {
		swapRun(rk, rs, rv, rt, 0, end)
		siftMaxRun(rk, rs, rv, rt, 0, end)
	}
}

func heapLess(allK, allS []int64, runPos []int, ra, rb int) bool {
	pa := runPos[ra]
	pb := runPos[rb]
	return lessRec(allK[pa], allS[pa], allK[pb], allS[pb])
}

func siftMinMerge(heap []int, hsz int, allK, allS []int64, runPos []int) {
	i := 0
	for {
		l := i*2 + 1
		if l >= hsz {
			break
		}
		best := l
		rr := l + 1
		if rr < hsz && heapLess(allK, allS, runPos, heap[rr], heap[best]) {
			best = rr
		}
		if heapLess(allK, allS, runPos, heap[best], heap[i]) {
			heap[i], heap[best] = heap[best], heap[i]
			i = best
		} else {
			break
		}
	}
}

func main() {
	var rng int64 = 555123456
	var globalSeq int64 = 1
	var l1K []int64
	var l1V []int64
	var hits int64
	var ck int64

	rk := make([]int64, 12000)
	rs := make([]int64, 12000)
	rv := make([]int64, 12000)
	rt := make([]int64, 12000)

	for cyc := 0; cyc < 4; cyc++ {
		allK := make([]int64, 0, 120000)
		allS := make([]int64, 0, 120000)
		allV := make([]int64, 0, 120000)
		allT := make([]int64, 0, 120000)
		runPos := make([]int, 0, 9)
		runEnd := make([]int, 0, 9)

		for rn := 0; rn < 8; rn++ {
			for j := 0; j < 12000; j++ {
				rng = (rng*1103515245 + 12345) & 2147483647
				k := rng % 40000
				rng = (rng*1103515245 + 12345) & 2147483647
				var tomb int64
				if (rng % 10) == 0 {
					tomb = 1
				}
				var val int64
				if tomb == 0 {
					rng = (rng*1103515245 + 12345) & 2147483647
					val = 1 + (rng % 100000)
				}
				rk[j] = k
				rs[j] = globalSeq
				rv[j] = val
				rt[j] = tomb
				globalSeq++
			}
			heapsortRun(rk, rs, rv, rt, 12000)
			st := len(allK)
			var prevK int64 = -1
			for j := 0; j < 12000; j++ {
				if rk[j] != prevK {
					allK = append(allK, rk[j])
					allS = append(allS, rs[j])
					allV = append(allV, rv[j])
					allT = append(allT, rt[j])
					prevK = rk[j]
				}
			}
			runPos = append(runPos, st)
			runEnd = append(runEnd, len(allK))
		}

		if len(l1K) > 0 {
			st := len(allK)
			for j := 0; j < len(l1K); j++ {
				allK = append(allK, l1K[j])
				allS = append(allS, 0)
				allV = append(allV, l1V[j])
				allT = append(allT, 0)
			}
			runPos = append(runPos, st)
			runEnd = append(runEnd, len(allK))
		}

		heap := make([]int, 0, len(runPos))
		for r := 0; r < len(runPos); r++ {
			if runPos[r] < runEnd[r] {
				heap = append(heap, r)
				hi := len(heap) - 1
				for hi > 0 {
					p := (hi - 1) >> 1
					if heapLess(allK, allS, runPos, heap[hi], heap[p]) {
						heap[hi], heap[p] = heap[p], heap[hi]
						hi = p
					} else {
						break
					}
				}
			}
		}

		newK := make([]int64, 0, 40000)
		newV := make([]int64, 0, 40000)
		var lastK int64 = -1
		hsz := len(heap)
		for hsz > 0 {
			topR := heap[0]
			pos := runPos[topR]
			k := allK[pos]
			v := allV[pos]
			t := allT[pos]
			runPos[topR] = pos + 1
			if runPos[topR] < runEnd[topR] {
				siftMinMerge(heap, hsz, allK, allS, runPos)
			} else {
				hsz--
				if hsz > 0 {
					heap[0] = heap[hsz]
					siftMinMerge(heap, hsz, allK, allS, runPos)
				}
			}
			if k != lastK {
				lastK = k
				if t == 0 {
					newK = append(newK, k)
					newV = append(newV, v)
				}
			}
		}

		l1K = newK
		l1V = newV
		nL1 := len(l1K)
		ck = (ck*37 + int64(nL1)) % modV

		for q := 0; q < 60000; q++ {
			rng = (rng*1103515245 + 12345) & 2147483647
			qk := rng % 40000
			lo := 0
			hi := nL1
			for lo < hi {
				mid := (lo + hi) >> 1
				if l1K[mid] < qk {
					lo = mid + 1
				} else {
					hi = mid
				}
			}
			if lo < nL1 && l1K[lo] == qk {
				hits++
				ck = (ck*31 + l1V[lo]) % modV
			}
		}
	}

	fmt.Printf("%d\n%d\n", hits, ck)
}
