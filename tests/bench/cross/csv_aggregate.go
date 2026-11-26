package main

import "fmt"

func main() {
	prefixes := []string{
		"tokyo", "oslo", "lima", "cairo", "paris", "rome", "zurich", "seoul",
		"bergen", "kyoto", "milan", "vienna", "prague", "dublin", "lisbon", "athens",
	}
	stBytes := make([]int64, 0, 1024)
	var stOff [64]int64
	var stLen [64]int64
	for i := int64(0); i < 64; i++ {
		p := prefixes[i&15]
		stOff[i] = int64(len(stBytes))
		for ci := 0; ci < len(p); ci++ {
			stBytes = append(stBytes, int64(p[ci]))
		}
		stBytes = append(stBytes, 95, 48+(i/10), 48+(i%10))
		stLen[i] = int64(len(stBytes)) - stOff[i]
	}

	buf := make([]int64, 0, 1600000)
	var digs [16]int64
	var rng int64 = 135792468
	for ri := 0; ri < 100000; ri++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		si := (rng >> 10) & 63
		rng = (rng*1103515245 + 12345) & 2147483647
		temp := (rng % 1999) - 999
		off := stOff[si]
		ln := stLen[si]
		for k := int64(0); k < ln; k++ {
			buf = append(buf, stBytes[off+k])
		}
		buf = append(buf, 59)
		av := temp
		if av < 0 {
			buf = append(buf, 45)
			av = -av
		}
		whole := av / 10
		if whole == 0 {
			buf = append(buf, 48)
		} else {
			w := whole
			dc := 0
			for w > 0 {
				digs[dc] = 48 + (w % 10)
				dc++
				w /= 10
			}
			for di := dc - 1; di >= 0; di-- {
				buf = append(buf, digs[di])
			}
		}
		buf = append(buf, 46, 48+(av%10), 10)
	}

	n := int64(len(buf))
	var firstDot int64
	for firstDot < n && buf[firstDot] != 46 {
		firstDot++
	}
	origFrac := buf[firstDot+1] - 48

	const (
		CAP  = 256
		MASK = 255
	)
	var kStart, kLen, stMin, stMax, stSum, stCnt, occ [256]int64

	var totRows int64
	var totCk int64
	for rd := int64(0); rd < 10; rd++ {
		buf[firstDot+1] = 48 + ((origFrac + rd) % 10)
		for i := 0; i < CAP; i++ {
			kStart[i] = -1
		}
		var pos int64
		var rows int64
		for pos < n {
			sStart := pos
			var h int64
			for buf[pos] != 59 {
				h = (h*131 + buf[pos]) & 2147483647
				pos++
			}
			sLen := pos - sStart
			pos++
			neg := false
			if buf[pos] == 45 {
				neg = true
				pos++
			}
			var v int64
			for buf[pos] != 46 {
				v = v*10 + (buf[pos] - 48)
				pos++
			}
			pos++
			v = v*10 + (buf[pos] - 48)
			pos++
			if neg {
				v = -v
			}
			if pos < n && buf[pos] == 10 {
				pos++
			}
			rows++

			slot := h & MASK
			for {
				ks := kStart[slot]
				if ks == -1 {
					kStart[slot] = sStart
					kLen[slot] = sLen
					stMin[slot] = v
					stMax[slot] = v
					stSum[slot] = v
					stCnt[slot] = 1
					break
				}
				if kLen[slot] == sLen {
					eq := true
					for ci := int64(0); ci < sLen; ci++ {
						if buf[ks+ci] != buf[sStart+ci] {
							eq = false
							break
						}
					}
					if eq {
						if v < stMin[slot] {
							stMin[slot] = v
						}
						if v > stMax[slot] {
							stMax[slot] = v
						}
						stSum[slot] += v
						stCnt[slot]++
						break
					}
				}
				slot = (slot + 1) & MASK
			}
		}

		var occLen int64
		for i := int64(0); i < CAP; i++ {
			if kStart[i] != -1 {
				occ[occLen] = i
				occLen++
			}
		}
		for i := int64(1); i < occLen; i++ {
			keySlot := occ[i]
			j := i - 1
			for j >= 0 {
				a := occ[j]
				la := kLen[a]
				lb := kLen[keySlot]
				ml := la
				if lb < ml {
					ml = lb
				}
				var cmp int64
				for t := int64(0); t < ml; t++ {
					ba := buf[kStart[a]+t]
					bb := buf[kStart[keySlot]+t]
					if ba != bb {
						if ba < bb {
							cmp = -1
						} else {
							cmp = 1
						}
						break
					}
				}
				if cmp == 0 {
					if la < lb {
						cmp = -1
					} else if la > lb {
						cmp = 1
					}
				}
				if cmp > 0 {
					occ[j+1] = occ[j]
					j--
				} else {
					break
				}
			}
			occ[j+1] = keySlot
		}

		var ck int64
		for i := int64(0); i < occLen; i++ {
			sl := occ[i]
			sMod := stSum[sl] % 1000000007
			if sMod < 0 {
				sMod += 1000000007
			}
			term := ((i+1)*7 + (stMin[sl]+1000)*13 + (stMax[sl]+1000)*17 + stCnt[sl]*19 + sMod) % 1000000007
			ck = (ck*1000003 + term) % 1000000007
		}
		totRows += rows
		totCk = (totCk*31 + ck) % 1000000007
	}
	fmt.Println(totRows)
	fmt.Println(totCk)
}
