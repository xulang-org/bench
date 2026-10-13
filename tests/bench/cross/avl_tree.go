package main

import "fmt"

type AVL struct {
	keys    []int64
	vals    []int64
	heights []int32
	lefts   []int32
	rights  []int32
	count   int32
	root    int32
}

func newAVL(cap int) AVL {
	return AVL{
		keys:    make([]int64, cap),
		vals:    make([]int64, cap),
		heights: make([]int32, cap),
		lefts:   make([]int32, cap),
		rights:  make([]int32, cap),
		count:   0,
		root:    -1,
	}
}

func (t *AVL) getH(idx int32) int32 {
	if idx == -1 {
		return 0
	}
	return t.heights[idx]
}

func (t *AVL) upd(idx int32) {
	hl := t.getH(t.lefts[idx])
	hr := t.getH(t.rights[idx])
	maxH := hr
	if hl > hr {
		maxH = hl
	}
	t.heights[idx] = 1 + maxH
}

func (t *AVL) bf(idx int32) int32 {
	return t.getH(t.lefts[idx]) - t.getH(t.rights[idx])
}

func (t *AVL) rotR(y int32) int32 {
	x := t.lefts[y]
	t2 := t.rights[x]
	t.rights[x] = y
	t.lefts[y] = t2
	t.upd(y)
	t.upd(x)
	return x
}

func (t *AVL) rotL(x int32) int32 {
	y := t.rights[x]
	t2 := t.lefts[y]
	t.lefts[y] = x
	t.rights[x] = t2
	t.upd(x)
	t.upd(y)
	return y
}

func (t *AVL) insert(idx int32, key, val int64) int32 {
	if idx == -1 {
		nid := t.count
		t.count++
		t.keys[nid] = key
		t.vals[nid] = val
		t.heights[nid] = 1
		t.lefts[nid] = -1
		t.rights[nid] = -1
		return nid
	}
	if key < t.keys[idx] {
		t.lefts[idx] = t.insert(t.lefts[idx], key, val)
	} else if key > t.keys[idx] {
		t.rights[idx] = t.insert(t.rights[idx], key, val)
	} else {
		t.vals[idx] = val
		return idx
	}
	t.upd(idx)
	b := t.bf(idx)
	if b > 1 && key < t.keys[t.lefts[idx]] {
		return t.rotR(idx)
	}
	if b < -1 && key > t.keys[t.rights[idx]] {
		return t.rotL(idx)
	}
	if b > 1 && key > t.keys[t.lefts[idx]] {
		t.lefts[idx] = t.rotL(t.lefts[idx])
		return t.rotR(idx)
	}
	if b < -1 && key < t.keys[t.rights[idx]] {
		t.rights[idx] = t.rotR(t.rights[idx])
		return t.rotL(idx)
	}
	return idx
}

func (t *AVL) search(key int64) int64 {
	cur := t.root
	for cur != -1 {
		k := t.keys[cur]
		if key == k {
			return t.vals[cur]
		} else if key < k {
			cur = t.lefts[cur]
		} else {
			cur = t.rights[cur]
		}
	}
	return 0
}

func main() {
	t := newAVL(100000)
	var seed int64 = 123456789
	for i := 0; i < 80000; i++ {
		seed = (seed*1103515245 + 12345) & 0x7fffffff
		k := seed % 200000
		v := (int64(i)*3 + 7) & 0x7fffffff
		t.root = t.insert(t.root, k, v)
	}

	var checksum int64 = 0
	for i := 0; i < 300000; i++ {
		seed = (seed*1103515245 + 12345) & 0x7fffffff
		k := seed % 200000
		val := t.search(k)
		checksum = (checksum*31 + val) % 1000000007
	}
	fmt.Println(checksum)
}
