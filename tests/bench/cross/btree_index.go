package main

import "fmt"

const modV int64 = 1000000007

type bPlusTree struct {
	isLeaf   []int64
	nkeys    []int64
	nextLeaf []int64
	keys     []int64
	vals     []int64
	children []int64
	pathNode []int
	pathIdx  []int
	root     int
}

func allocNode(t *bPlusTree, leaf int64) int {
	u := len(t.isLeaf)
	t.isLeaf = append(t.isLeaf, leaf)
	t.nkeys = append(t.nkeys, 0)
	t.nextLeaf = append(t.nextLeaf, -1)
	for j := 0; j < 32; j++ {
		t.keys = append(t.keys, 0)
		t.vals = append(t.vals, 0)
	}
	for c := 0; c < 33; c++ {
		t.children = append(t.children, -1)
	}
	return u
}

func newBTree() *bPlusTree {
	t := &bPlusTree{
		pathNode: make([]int, 16),
		pathIdx:  make([]int, 16),
	}
	t.root = allocNode(t, 1)
	return t
}

func descendLeaf(t *bPlusTree, k int64) int {
	u := t.root
	for t.isLeaf[u] == 0 {
		base := u * 32
		lo := 0
		hi := int(t.nkeys[u])
		for lo < hi {
			mid := (lo + hi) >> 1
			if t.keys[base+mid] <= k {
				lo = mid + 1
			} else {
				hi = mid
			}
		}
		u = int(t.children[u*33+lo])
	}
	return u
}

func btInsert(t *bPlusTree, k, v int64) {
	u := t.root
	depth := 0
	for t.isLeaf[u] == 0 {
		base := u * 32
		lo := 0
		hi := int(t.nkeys[u])
		for lo < hi {
			mid := (lo + hi) >> 1
			if t.keys[base+mid] <= k {
				lo = mid + 1
			} else {
				hi = mid
			}
		}
		t.pathNode[depth] = u
		t.pathIdx[depth] = lo
		depth++
		u = int(t.children[u*33+lo])
	}

	base := u * 32
	n := int(t.nkeys[u])
	lo := 0
	hi := n
	for lo < hi {
		mid := (lo + hi) >> 1
		if t.keys[base+mid] < k {
			lo = mid + 1
		} else {
			hi = mid
		}
	}
	if lo < n && t.keys[base+lo] == k {
		t.vals[base+lo] = v
		return
	}
	for j := n; j > lo; j-- {
		t.keys[base+j] = t.keys[base+j-1]
		t.vals[base+j] = t.vals[base+j-1]
	}
	t.keys[base+lo] = k
	t.vals[base+lo] = v
	n++
	t.nkeys[u] = int64(n)
	if n < 32 {
		return
	}

	r := allocNode(t, 1)
	rbase := r * 32
	for j := 0; j < 16; j++ {
		t.keys[rbase+j] = t.keys[base+16+j]
		t.vals[rbase+j] = t.vals[base+16+j]
	}
	t.nkeys[u] = 16
	t.nkeys[r] = 16
	t.nextLeaf[r] = t.nextLeaf[u]
	t.nextLeaf[u] = int64(r)
	upKey := t.keys[rbase]
	upRight := int64(r)

	for d := depth - 1; d >= 0; d-- {
		p := t.pathNode[d]
		ins := t.pathIdx[d]
		pbase := p * 32
		pcbase := p * 33
		pn := int(t.nkeys[p])
		for kIdx := pn; kIdx > ins; kIdx-- {
			t.keys[pbase+kIdx] = t.keys[pbase+kIdx-1]
			t.children[pcbase+kIdx+1] = t.children[pcbase+kIdx]
		}
		t.keys[pbase+ins] = upKey
		t.children[pcbase+ins+1] = upRight
		pn++
		t.nkeys[p] = int64(pn)
		if pn < 32 {
			return
		}
		nr := allocNode(t, 0)
		nrbase := nr * 32
		nrcbase := nr * 33
		midKey := t.keys[pbase+16]
		for m := 0; m < 15; m++ {
			t.keys[nrbase+m] = t.keys[pbase+17+m]
		}
		for c := 0; c < 16; c++ {
			t.children[nrcbase+c] = t.children[pcbase+17+c]
		}
		t.nkeys[p] = 16
		t.nkeys[nr] = 15
		upKey = midKey
		upRight = int64(nr)
	}

	newRoot := allocNode(t, 0)
	t.keys[newRoot*32] = upKey
	t.children[newRoot*33] = int64(t.root)
	t.children[newRoot*33+1] = upRight
	t.nkeys[newRoot] = 1
	t.root = newRoot
}

func btLookup(t *bPlusTree, k int64) int64 {
	u := descendLeaf(t, k)
	base := u * 32
	n := int(t.nkeys[u])
	lo := 0
	hi := n
	for lo < hi {
		mid := (lo + hi) >> 1
		if t.keys[base+mid] < k {
			lo = mid + 1
		} else {
			hi = mid
		}
	}
	if lo < n && t.keys[base+lo] == k {
		return t.vals[base+lo]
	}
	return -1
}

func main() {
	t := newBTree()
	var rng int64 = 123456789

	for i := int64(0); i < 80000; i++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		k := rng % 1000000
		rng = (rng*1103515245 + 12345) & 2147483647
		v := (i*17 + (rng & 1023)) % 1000000
		btInsert(t, k, v)
	}

	var hits int64
	var ck int64
	for q := 0; q < 120000; q++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		k := rng % 1000000
		v := btLookup(t, k)
		if v >= 0 {
			hits++
			ck = (ck*31 + v) % modV
		}
	}

	var rcnt int64
	for r := 0; r < 2000; r++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		loK := rng % 999000
		hiK := loK + 1000
		u := descendLeaf(t, loK)
		base0 := u * 32
		n0 := int(t.nkeys[u])
		lo := 0
		hi := n0
		for lo < hi {
			mid := (lo + hi) >> 1
			if t.keys[base0+mid] < loK {
				lo = mid + 1
			} else {
				hi = mid
			}
		}
		var cnt int64
		var s int64
		idx := lo
		for u != -1 {
			base := u * 32
			n := int(t.nkeys[u])
			done := false
			for j := idx; j < n; j++ {
				if t.keys[base+j] > hiK {
					done = true
					break
				}
				cnt++
				s = (s + t.vals[base+j]) % modV
			}
			if done {
				break
			}
			u = int(t.nextLeaf[u])
			idx = 0
		}
		rcnt += cnt
		ck = (ck*37 + s + cnt) % modV
	}

	fmt.Printf("%d\n%d\n", hits+rcnt, ck)
}
