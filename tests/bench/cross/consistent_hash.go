package main

import "fmt"

const modV int64 = 1000000007

func mix32(x int64) int64 {
	const mask int64 = 4294967295
	const mul int64 = 73244475
	h := x & mask
	h = h ^ (h >> 16)
	h = (h * mul) & mask
	h = h ^ (h >> 16)
	h = (h * mul) & mask
	h = h ^ (h >> 16)
	return h
}

func siftMaxRing(rt, rn []int64, start, n int) {
	i := start
	for {
		l := i*2 + 1
		if l >= n {
			break
		}
		best := l
		r := l + 1
		if r < n && rt[r] > rt[best] {
			best = r
		}
		if rt[i] < rt[best] {
			rt[i], rt[best] = rt[best], rt[i]
			rn[i], rn[best] = rn[best], rn[i]
			i = best
		} else {
			break
		}
	}
}

func heapsortRing(rt, rn []int64, n int) {
	for start := n/2 - 1; start >= 0; start-- {
		siftMaxRing(rt, rn, start, n)
	}
	for end := n - 1; end > 0; end-- {
		rt[0], rt[end] = rt[end], rt[0]
		rn[0], rn[end] = rn[end], rn[0]
		siftMaxRing(rt, rn, 0, end)
	}
}

func buildRing(alive []int64, ringTok, ringNode []int64) int {
	const maxNodes = 48
	const vnodes = 128
	const goldC int64 = 2654435769
	sz := 0
	for nid := 0; nid < maxNodes; nid++ {
		if alive[nid] == 1 {
			for v := 0; v < vnodes; v++ {
				ringTok[sz] = mix32(((int64(nid) << 10) | int64(v)) ^ goldC)
				ringNode[sz] = int64(nid)
				sz++
			}
		}
	}
	heapsortRing(ringTok, ringNode, sz)
	return sz
}

func routeTok(ringTok, ringNode []int64, tok int64, sz int) int64 {
	lo := 0
	hi := sz
	for lo < hi {
		mid := (lo + hi) >> 1
		if ringTok[mid] < tok {
			lo = mid + 1
		} else {
			hi = mid
		}
	}
	if lo == sz {
		lo = 0
	}
	return ringNode[lo]
}

func main() {
	const mask32 int64 = 4294967295
	const maxNodes = 48
	const vnodes = 128
	const nKeys = 150000

	alive := make([]int64, maxNodes)
	nodeLoad := make([]int64, maxNodes)
	for nid := 0; nid < 32; nid++ {
		alive[nid] = 1
	}

	ringTok := make([]int64, maxNodes*vnodes)
	ringNode := make([]int64, maxNodes*vnodes)
	keyTok := make([]int64, nKeys)
	prevOwner := make([]int64, nKeys)

	for i := 0; i < nKeys; i++ {
		keyTok[i] = mix32((int64(i)*2654435761 + 12345) & mask32)
	}

	ringSz := buildRing(alive, ringTok, ringNode)
	var ck int64
	for p := int64(0); p < 4; p++ {
		salt := p * 7919
		for i := 0; i < nKeys; i++ {
			t := mix32((keyTok[i] + salt) & mask32)
			owner := routeTok(ringTok, ringNode, t, ringSz)
			nodeLoad[owner]++
			ck = (ck*31 + owner + 1) % modV
		}
	}

	for i := 0; i < nKeys; i++ {
		prevOwner[i] = routeTok(ringTok, ringNode, keyTok[i], ringSz)
	}

	var totalMoved int64
	for step := 0; step < 4; step++ {
		if step == 0 {
			alive[32], alive[33], alive[34], alive[35] = 1, 1, 1, 1
		} else if step == 1 {
			alive[5], alive[19] = 0, 0
		} else if step == 2 {
			alive[36], alive[37], alive[38], alive[39], alive[40], alive[41] = 1, 1, 1, 1, 1, 1
		} else {
			alive[2], alive[11], alive[24], alive[33] = 0, 0, 0, 0
		}
		ringSz = buildRing(alive, ringTok, ringNode)
		var moved int64
		for i := 0; i < nKeys; i++ {
			o := routeTok(ringTok, ringNode, keyTok[i], ringSz)
			if o != prevOwner[i] {
				moved++
				prevOwner[i] = o
			}
			ck = (ck*31 + o + 1) % modV
		}
		totalMoved += moved
		ck = (ck*37 + moved) % modV
	}

	for nid := 0; nid < maxNodes; nid++ {
		ck = (ck*31 + nodeLoad[nid]) % modV
	}

	fmt.Printf("%d\n%d\n", totalMoved, ck)
}
