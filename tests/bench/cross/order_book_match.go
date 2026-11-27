package main

import "fmt"

const modV int64 = 1000000007

type orderBook struct {
	bHead []int
	bTail []int
	aHead []int
	aTail []int
	oSide []int
	oPx   []int
	oQty  []int64
	oAct  []int
	oPrev []int
	oNext []int
}

func newBook(pmax, maxOrd int) *orderBook {
	ob := &orderBook{
		bHead: make([]int, pmax),
		bTail: make([]int, pmax),
		aHead: make([]int, pmax),
		aTail: make([]int, pmax),
		oSide: make([]int, maxOrd),
		oPx:   make([]int, maxOrd),
		oQty:  make([]int64, maxOrd),
		oAct:  make([]int, maxOrd),
		oPrev: make([]int, maxOrd),
		oNext: make([]int, maxOrd),
	}
	for i := 0; i < pmax; i++ {
		ob.bHead[i] = -1
		ob.bTail[i] = -1
		ob.aHead[i] = -1
		ob.aTail[i] = -1
	}
	for i := 0; i < maxOrd; i++ {
		ob.oPrev[i] = -1
		ob.oNext[i] = -1
	}
	return ob
}

func pushBook(ob *orderBook, head, tail []int, px, oid int) {
	t := tail[px]
	ob.oPrev[oid] = t
	ob.oNext[oid] = -1
	if t != -1 {
		ob.oNext[t] = oid
	} else {
		head[px] = oid
	}
	tail[px] = oid
}

func unlinkBook(ob *orderBook, head, tail []int, px, oid int) {
	pr := ob.oPrev[oid]
	nx := ob.oNext[oid]
	if pr != -1 {
		ob.oNext[pr] = nx
	} else {
		head[px] = nx
	}
	if nx != -1 {
		ob.oPrev[nx] = pr
	} else {
		tail[px] = pr
	}
	ob.oPrev[oid] = -1
	ob.oNext[oid] = -1
}

func main() {
	const pmax = 2048
	const maxOrd = 262144
	ob := newBook(pmax, maxOrd)
	var rng int64 = 70707070

	bestBid := -1
	bestAsk := pmax
	nextID := 0
	var trades int64
	var cancels int64
	var ck int64

	for ev := 0; ev < 250000; ev++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		r := rng % 10
		if r < 2 && nextID > 0 {
			win := nextID
			if win > 4096 {
				win = 4096
			}
			rng = (rng*1103515245 + 12345) & 2147483647
			cid := nextID - 1 - int(rng%int64(win))
			if ob.oAct[cid] == 1 {
				px := ob.oPx[cid]
				if ob.oSide[cid] == 0 {
					unlinkBook(ob, ob.bHead, ob.bTail, px, cid)
					if px == bestBid && ob.bHead[px] == -1 {
						for bestBid >= 0 && ob.bHead[bestBid] == -1 {
							bestBid--
						}
					}
				} else {
					unlinkBook(ob, ob.aHead, ob.aTail, px, cid)
					if px == bestAsk && ob.aHead[px] == -1 {
						for bestAsk < pmax && ob.aHead[bestAsk] == -1 {
							bestAsk++
						}
					}
				}
				ob.oAct[cid] = 0
				cancels++
			}
		} else {
			rng = (rng*1103515245 + 12345) & 2147483647
			side := (rng >> 16) & 1
			mid := 1024
			if bestBid >= 0 && bestAsk < pmax {
				mid = (bestBid + bestAsk) >> 1
			} else if bestBid >= 0 {
				mid = bestBid
			} else if bestAsk < pmax {
				mid = bestAsk
			}
			rng = (rng*1103515245 + 12345) & 2147483647
			px := mid + int(rng%41) - 20
			if px < 1 {
				px = 1
			}
			if px > pmax-2 {
				px = pmax - 2
			}
			rng = (rng*1103515245 + 12345) & 2147483647
			qty := 1 + (rng % 50)
			if side == 0 {
				for qty > 0 && bestAsk <= px {
					oid := ob.aHead[bestAsk]
					fill := ob.oQty[oid]
					if qty < fill {
						fill = qty
					}
					qty -= fill
					ob.oQty[oid] -= fill
					trades++
					ck = (ck*31 + fill*1009 + int64(bestAsk)) % modV
					if ob.oQty[oid] == 0 {
						unlinkBook(ob, ob.aHead, ob.aTail, bestAsk, oid)
						ob.oAct[oid] = 0
						if ob.aHead[bestAsk] == -1 {
							for bestAsk < pmax && ob.aHead[bestAsk] == -1 {
								bestAsk++
							}
						}
					}
				}
				if qty > 0 {
					oid := nextID
					nextID++
					ob.oSide[oid] = 0
					ob.oPx[oid] = px
					ob.oQty[oid] = qty
					ob.oAct[oid] = 1
					pushBook(ob, ob.bHead, ob.bTail, px, oid)
					if px > bestBid {
						bestBid = px
					}
				}
			} else {
				for qty > 0 && bestBid >= px {
					oid := ob.bHead[bestBid]
					fill := ob.oQty[oid]
					if qty < fill {
						fill = qty
					}
					qty -= fill
					ob.oQty[oid] -= fill
					trades++
					ck = (ck*31 + fill*1009 + int64(bestBid)) % modV
					if ob.oQty[oid] == 0 {
						unlinkBook(ob, ob.bHead, ob.bTail, bestBid, oid)
						ob.oAct[oid] = 0
						if ob.bHead[bestBid] == -1 {
							for bestBid >= 0 && ob.bHead[bestBid] == -1 {
								bestBid--
							}
						}
					}
				}
				if qty > 0 {
					oid := nextID
					nextID++
					ob.oSide[oid] = 1
					ob.oPx[oid] = px
					ob.oQty[oid] = qty
					ob.oAct[oid] = 1
					pushBook(ob, ob.aHead, ob.aTail, px, oid)
					if px < bestAsk {
						bestAsk = px
					}
				}
			}
		}
	}

	ck = (ck*37 + cancels*17 + int64(bestBid+1)*7 + int64(bestAsk)) % modV
	fmt.Printf("%d\n%d\n", trades, ck)
}
