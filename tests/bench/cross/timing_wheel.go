package main

import "fmt"

const modV int64 = 1000000007

type wheel struct {
	tExp      []int64
	tPer      []int64
	tRep      []int
	tPay      []int64
	tSt       []int
	tPrev     []int
	tNext     []int
	tBkt      []int
	bHead     []int
	bTail     []int
	freeStack []int
	freeTop   int
}

func newWheel() *wheel {
	const maxNodes = 131072
	w := &wheel{
		tExp:      make([]int64, maxNodes),
		tPer:      make([]int64, maxNodes),
		tRep:      make([]int, maxNodes),
		tPay:      make([]int64, maxNodes),
		tSt:       make([]int, maxNodes),
		tPrev:     make([]int, maxNodes),
		tNext:     make([]int, maxNodes),
		tBkt:      make([]int, maxNodes),
		bHead:     make([]int, 512),
		bTail:     make([]int, 512),
		freeStack: make([]int, maxNodes),
		freeTop:   maxNodes,
	}
	for i := 0; i < maxNodes; i++ {
		w.tPrev[i] = -1
		w.tNext[i] = -1
		w.tBkt[i] = -1
		w.freeStack[i] = maxNodes - 1 - i
	}
	for i := 0; i < 512; i++ {
		w.bHead[i] = -1
		w.bTail[i] = -1
	}
	return w
}

func bktPush(w *wheel, b, u int) {
	tail := w.bTail[b]
	w.tPrev[u] = tail
	w.tNext[u] = -1
	w.tBkt[u] = b
	if tail != -1 {
		w.tNext[tail] = u
	} else {
		w.bHead[b] = u
	}
	w.bTail[b] = u
}

func bktRemove(w *wheel, u int) {
	b := w.tBkt[u]
	pr := w.tPrev[u]
	nx := w.tNext[u]
	if pr != -1 {
		w.tNext[pr] = nx
	} else {
		w.bHead[b] = nx
	}
	if nx != -1 {
		w.tPrev[nx] = pr
	} else {
		w.bTail[b] = pr
	}
	w.tPrev[u] = -1
	w.tNext[u] = -1
	w.tBkt[u] = -1
}

func scheduleNode(w *wheel, u int, exp, now int64) {
	w.tExp[u] = exp
	w.tSt[u] = 1
	if (exp - now) < 256 {
		bktPush(w, int(exp&255), u)
	} else {
		bktPush(w, 256+int((exp>>8)&255), u)
	}
}

func main() {
	const ringH = 16384
	w := newWheel()
	var rng int64 = 888777666

	handles := make([]int, ringH)
	for i := 0; i < ringH; i++ {
		handles[i] = -1
	}

	hWr := 0
	var fired int64
	var canceled int64
	var ck int64

	for now := int64(0); now < 160000; now++ {
		for k := 0; k < 3; k++ {
			if w.freeTop > 0 {
				w.freeTop--
				u := w.freeStack[w.freeTop]
				rng = (rng*1103515245 + 12345) & 2147483647
				var delay int64
				if (rng % 10) < 6 {
					rng = (rng*1103515245 + 12345) & 2147483647
					delay = 1 + (rng % 250)
				} else {
					rng = (rng*1103515245 + 12345) & 2147483647
					delay = 256 + (rng % 4096)
				}
				rng = (rng*1103515245 + 12345) & 2147483647
				var per int64
				rep := 0
				if (rng % 5) == 0 {
					rng = (rng*1103515245 + 12345) & 2147483647
					per = 17 + (rng % 200)
					rep = 2
				}
				rng = (rng*1103515245 + 12345) & 2147483647
				pay := rng % 100000
				w.tPer[u] = per
				w.tRep[u] = rep
				w.tPay[u] = pay
				scheduleNode(w, u, now+delay, now)
				handles[hWr] = u
				hWr = (hWr + 1) & 16383
			}
		}

		rng = (rng*1103515245 + 12345) & 2147483647
		ci := int(rng & 16383)
		cu := handles[ci]
		if cu != -1 && w.tSt[cu] == 1 {
			bktRemove(w, cu)
			w.tSt[cu] = 0
			w.freeStack[w.freeTop] = cu
			w.freeTop++
			handles[ci] = -1
			canceled++
		}

		tick := now + 1
		if (tick & 255) == 0 {
			cb := 256 + int((tick>>8)&255)
			u := w.bHead[cb]
			w.bHead[cb] = -1
			w.bTail[cb] = -1
			for u != -1 {
				nx := w.tNext[u]
				w.tPrev[u] = -1
				w.tNext[u] = -1
				w.tBkt[u] = -1
				bktPush(w, int(w.tExp[u]&255), u)
				u = nx
			}
		}

		b0 := int(tick & 255)
		u := w.bHead[b0]
		w.bHead[b0] = -1
		w.bTail[b0] = -1
		for u != -1 {
			nx := w.tNext[u]
			w.tPrev[u] = -1
			w.tNext[u] = -1
			w.tBkt[u] = -1
			fired++
			ck = (ck*31 + w.tPay[u]*7 + tick) % modV
			if w.tRep[u] > 0 {
				w.tRep[u]--
				scheduleNode(w, u, tick+w.tPer[u], tick)
			} else {
				w.tSt[u] = 0
				w.freeStack[w.freeTop] = u
				w.freeTop++
			}
			u = nx
		}
	}

	ck = (ck*37 + canceled) % modV
	fmt.Printf("%d\n%d\n", fired, ck)
}
