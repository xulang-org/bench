package main

import "fmt"

type Pair struct {
	l int64
	r int64
}

type Treap struct {
	key      []int64
	pri      []int64
	left     []int64
	right    []int64
	freeHead int64
	root     int64
	size     int64
}

func newTreap() Treap {
	return Treap{
		key:      make([]int64, 0, 32768),
		pri:      make([]int64, 0, 32768),
		left:     make([]int64, 0, 32768),
		right:    make([]int64, 0, 32768),
		freeHead: -1,
		root:     -1,
		size:     0,
	}
}

func (t *Treap) allocNode(k, p int64) int64 {
	if t.freeHead != -1 {
		idx := t.freeHead
		t.freeHead = t.left[idx]
		t.key[idx] = k
		t.pri[idx] = p
		t.left[idx] = -1
		t.right[idx] = -1
		return idx
	}
	idx := int64(len(t.key))
	t.key = append(t.key, k)
	t.pri = append(t.pri, p)
	t.left = append(t.left, -1)
	t.right = append(t.right, -1)
	return idx
}

func (t *Treap) freeNode(idx int64) {
	t.left[idx] = t.freeHead
	t.right[idx] = -1
	t.freeHead = idx
}

func (t *Treap) split(u, k int64) Pair {
	if u == -1 {
		return Pair{-1, -1}
	}
	if t.key[u] < k {
		p := t.split(t.right[u], k)
		t.right[u] = p.l
		return Pair{u, p.r}
	}
	p := t.split(t.left[u], k)
	t.left[u] = p.r
	return Pair{p.l, u}
}

func (t *Treap) merge(a, b int64) int64 {
	if a == -1 {
		return b
	}
	if b == -1 {
		return a
	}
	if t.pri[a] > t.pri[b] {
		t.right[a] = t.merge(t.right[a], b)
		return a
	}
	t.left[b] = t.merge(a, t.left[b])
	return b
}

func (t *Treap) contains(k int64) bool {
	u := t.root
	for u != -1 {
		ku := t.key[u]
		if k == ku {
			return true
		}
		if k < ku {
			u = t.left[u]
		} else {
			u = t.right[u]
		}
	}
	return false
}

func (t *Treap) insert(k, p int64) {
	if t.contains(k) {
		return
	}
	sp := t.split(t.root, k)
	n := t.allocNode(k, p)
	t.root = t.merge(t.merge(sp.l, n), sp.r)
	t.size++
}

func (t *Treap) erase(k int64) {
	sp1 := t.split(t.root, k)
	sp2 := t.split(sp1.r, k+1)
	if sp2.l != -1 {
		t.freeNode(sp2.l)
		t.size--
	}
	t.root = t.merge(sp1.l, sp2.r)
}

func main() {
	tr := newTreap()
	var rng int64 = 123456789
	var hits int64
	var ck int64
	for step := int64(0); step < 120000; step++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		op := rng % 10
		rng = (rng*1103515245 + 12345) & 2147483647
		k := rng % 40000
		if op < 4 {
			rng = (rng*1103515245 + 12345) & 2147483647
			tr.insert(k, rng)
		} else if op < 6 {
			tr.erase(k)
		} else {
			if tr.contains(k) {
				hits++
				ck = (ck*131 + k + 1) % 1000000007
			}
		}
	}
	fmt.Println(hits)
	fmt.Println(ck)
	fmt.Println(tr.size)
}
