package main

import "fmt"

const modV int64 = 1000000007

type slabArena struct {
	mem          []int64
	pageCls      []int
	pageUsed     []int
	pageHead     []int
	pagePrev     []int
	pageNext     []int
	pageInList   []int
	clsHead      []int
	freeStack    []int
	freeTop      int
	classSz      [6]int
	pageAllocs   int64
	pageReclaims int64
}

func newSlab() *slabArena {
	const nPages = 256
	s := &slabArena{
		mem:        make([]int64, nPages*256),
		pageCls:    make([]int, nPages),
		pageUsed:   make([]int, nPages),
		pageHead:   make([]int, nPages),
		pagePrev:   make([]int, nPages),
		pageNext:   make([]int, nPages),
		pageInList: make([]int, nPages),
		clsHead:    make([]int, 6),
		freeStack:  make([]int, nPages),
		freeTop:    nPages,
		classSz:    [6]int{2, 4, 8, 16, 32, 64},
	}
	for i := 0; i < nPages; i++ {
		s.pageCls[i] = -1
		s.pageHead[i] = -1
		s.pagePrev[i] = -1
		s.pageNext[i] = -1
		s.freeStack[i] = nPages - 1 - i
	}
	for i := 0; i < 6; i++ {
		s.clsHead[i] = -1
	}
	return s
}

func listPush(s *slabArena, cls, pg int) {
	h := s.clsHead[cls]
	s.pagePrev[pg] = -1
	s.pageNext[pg] = h
	if h != -1 {
		s.pagePrev[h] = pg
	}
	s.clsHead[cls] = pg
	s.pageInList[pg] = 1
}

func listRemove(s *slabArena, cls, pg int) {
	pr := s.pagePrev[pg]
	nx := s.pageNext[pg]
	if pr != -1 {
		s.pageNext[pr] = nx
	} else {
		s.clsHead[cls] = nx
	}
	if nx != -1 {
		s.pagePrev[nx] = pr
	}
	s.pagePrev[pg] = -1
	s.pageNext[pg] = -1
	s.pageInList[pg] = 0
}

func slabAlloc(s *slabArena, cls int) int {
	pg := s.clsHead[cls]
	if pg == -1 {
		if s.freeTop == 0 {
			return -1
		}
		s.freeTop--
		pg = s.freeStack[s.freeTop]
		s.pageAllocs++
		s.pageCls[pg] = cls
		s.pageUsed[pg] = 0
		sz := s.classSz[cls]
		base := pg << 8
		cnt := 256 / sz
		for j := 0; j < cnt-1; j++ {
			s.mem[base+j*sz] = int64(base + (j+1)*sz)
		}
		s.mem[base+(cnt-1)*sz] = -1
		s.pageHead[pg] = base
		listPush(s, cls, pg)
	}
	ptr := s.pageHead[pg]
	nxtPtr := int(s.mem[ptr])
	s.pageHead[pg] = nxtPtr
	s.pageUsed[pg]++
	if nxtPtr == -1 {
		listRemove(s, cls, pg)
	}
	return ptr
}

func slabFree(s *slabArena, ptr int) {
	pg := ptr >> 8
	cls := s.pageCls[pg]
	wasFull := 0
	if s.pageHead[pg] == -1 {
		wasFull = 1
	}
	s.mem[ptr] = int64(s.pageHead[pg])
	s.pageHead[pg] = ptr
	s.pageUsed[pg]--
	if s.pageUsed[pg] == 0 {
		if s.pageInList[pg] == 1 {
			listRemove(s, cls, pg)
		}
		s.pageCls[pg] = -1
		s.pageHead[pg] = -1
		s.freeStack[s.freeTop] = pg
		s.freeTop++
		s.pageReclaims++
	} else if wasFull == 1 {
		listPush(s, cls, pg)
	}
}

func main() {
	const live = 1024
	s := newSlab()
	var rng int64 = 31415926

	livePtr := make([]int, live)
	liveCls := make([]int, live)
	for i := 0; i < live; i++ {
		livePtr[i] = -1
	}

	var allocOk int64
	var ck int64
	for opI := int64(0); opI < 600000; opI++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		slot := int(rng & 1023)
		if (opI & 4095) == 4095 {
			for k := 0; k < live; k += 3 {
				p := livePtr[k]
				if p != -1 {
					sz := s.classSz[liveCls[k]]
					ck = (ck*31 + s.mem[p] + s.mem[p+sz-1]) % modV
					slabFree(s, p)
					livePtr[k] = -1
				}
			}
		}
		if livePtr[slot] != -1 {
			p := livePtr[slot]
			sz := s.classSz[liveCls[slot]]
			ck = (ck*31 + s.mem[p] + s.mem[p+sz-1]) % modV
			slabFree(s, p)
			livePtr[slot] = -1
		} else {
			rng = (rng*1103515245 + 12345) & 2147483647
			r := rng % 100
			cls := 5
			if r < 35 {
				cls = 0
			} else if r < 60 {
				cls = 1
			} else if r < 78 {
				cls = 2
			} else if r < 90 {
				cls = 3
			} else if r < 97 {
				cls = 4
			}
			p := slabAlloc(s, cls)
			if p >= 0 {
				sz := s.classSz[cls]
				tag := (opI*13 + int64(cls)*7 + 1) % modV
				s.mem[p] = tag
				s.mem[p+sz-1] = (tag ^ int64(p*3)) % modV
				livePtr[slot] = p
				liveCls[slot] = cls
				allocOk++
			}
		}
	}

	for k := 0; k < live; k++ {
		p := livePtr[k]
		if p != -1 {
			sz := s.classSz[liveCls[k]]
			ck = (ck*31 + s.mem[p] + s.mem[p+sz-1]) % modV
			slabFree(s, p)
			livePtr[k] = -1
		}
	}
	ck = (ck*37 + s.pageAllocs*17 + s.pageReclaims) % modV
	fmt.Printf("%d\n%d\n", allocOk, ck)
}
