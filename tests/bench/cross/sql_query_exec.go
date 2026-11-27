package main

import "fmt"

const modV int64 = 1000000007

func main() {
	const nCust = 8192
	const htCap = 16384
	const htMask int64 = 16383
	const nOrd = 200000
	var rng int64 = 42424242

	custId := make([]int64, nCust)
	custReg := make([]int64, nCust)
	custTier := make([]int64, nCust)
	htKey := make([]int64, htCap)
	htVal := make([]int, htCap)
	for i := 0; i < htCap; i++ {
		htKey[i] = -1
		htVal[i] = -1
	}

	for i := 0; i < nCust; i++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		cid := 100000 + int64(i)*7 + (rng % 5)
		custId[i] = cid
		rng = (rng*1103515245 + 12345) & 2147483647
		custReg[i] = rng % 16
		rng = (rng*1103515245 + 12345) & 2147483647
		custTier[i] = rng % 4
		slot := int(((cid * 2654435761) >> 16) & htMask)
		for htKey[slot] != -1 {
			slot = (slot + 1) & int(htMask)
		}
		htKey[slot] = cid
		htVal[slot] = i
	}

	ordCid := make([]int64, nOrd)
	ordCat := make([]int64, nOrd)
	ordAmt := make([]int64, nOrd)
	ordStatus := make([]int64, nOrd)
	for i := 0; i < nOrd; i++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		if (rng % 20) < 17 {
			rng = (rng*1103515245 + 12345) & 2147483647
			ordCid[i] = custId[rng%nCust]
		} else {
			rng = (rng*1103515245 + 12345) & 2147483647
			ordCid[i] = 9000000 + (rng % 50000)
		}
		rng = (rng*1103515245 + 12345) & 2147483647
		ordCat[i] = rng % 32
		rng = (rng*1103515245 + 12345) & 2147483647
		ordAmt[i] = 100 + (rng % 2000)
		rng = (rng*1103515245 + 12345) & 2147483647
		if (rng % 5) != 0 {
			ordStatus[i] = 1
		}
	}

	grpCnt := make([]int64, 512)
	grpRev := make([]int64, 512)
	active := make([]int, 512)
	var totalRows int64
	var ck int64

	for rnd := int64(0); rnd < 16; rnd++ {
		minAmt := 350 + rnd*50
		for b := 0; b < 512; b++ {
			grpCnt[b] = 0
			grpRev[b] = 0
		}
		for i := 0; i < nOrd; i++ {
			if ordStatus[i] != 1 {
				continue
			}
			amt := ordAmt[i]
			if amt < minAmt {
				continue
			}
			cid := ordCid[i]
			slot := int(((cid * 2654435761) >> 16) & htMask)
			found := -1
			for htKey[slot] != -1 {
				if htKey[slot] == cid {
					found = htVal[slot]
					break
				}
				slot = (slot + 1) & int(htMask)
			}
			if found == -1 {
				continue
			}
			tier := custTier[found]
			if tier == 0 {
				continue
			}
			gb := int(custReg[found]*32 + ordCat[i])
			grpCnt[gb]++
			grpRev[gb] += amt * tier
			totalRows++
		}

		acnt := 0
		for b := 0; b < 512; b++ {
			if grpCnt[b] > 0 {
				active[acnt] = b
				acnt++
			}
		}
		for i := 1; i < acnt; i++ {
			kb := active[i]
			kr := grpRev[kb]
			j := i - 1
			for j >= 0 {
				jb := active[j]
				jr := grpRev[jb]
				if jr < kr || (jr == kr && jb > kb) {
					active[j+1] = jb
					j--
				} else {
					break
				}
			}
			active[j+1] = kb
		}
		for i := 0; i < acnt; i++ {
			gb := active[i]
			row := (int64(gb)*1000003 + grpCnt[gb]*97 + (grpRev[gb] % modV)) % modV
			ck = (ck*31 + row) % modV
		}
	}

	fmt.Printf("%d\n%d\n", totalRows, ck)
}
