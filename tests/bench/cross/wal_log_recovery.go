package main

import "fmt"

const modV int64 = 1000000007

func crc32Slice(crcTbl, buf []int64, start, length int) int64 {
	const mask32 int64 = 4294967295
	c := mask32
	end := start + length
	for i := start; i < end; i++ {
		idx := (c ^ buf[i]) & 255
		c = crcTbl[idx] ^ (c >> 8)
	}
	return c ^ mask32
}

func kvPut(kvKey, kvVal []int64, k, v int64) {
	const kvMask int64 = 8191
	slot := int(((k * 2654435761) >> 16) & kvMask)
	firstTomb := -1
	for {
		cur := kvKey[slot]
		if cur == k {
			kvVal[slot] = v
			return
		}
		if cur == -1 {
			dst := slot
			if firstTomb != -1 {
				dst = firstTomb
			}
			kvKey[dst] = k
			kvVal[dst] = v
			return
		}
		if cur == -2 && firstTomb == -1 {
			firstTomb = slot
		}
		slot = (slot + 1) & int(kvMask)
	}
}

func kvDel(kvKey, kvVal []int64, k int64) {
	const kvMask int64 = 8191
	slot := int(((k * 2654435761) >> 16) & kvMask)
	for {
		cur := kvKey[slot]
		if cur == -1 {
			return
		}
		if cur == k {
			kvKey[slot] = -2
			kvVal[slot] = 0
			return
		}
		slot = (slot + 1) & int(kvMask)
	}
}

func kvGet(kvKey, kvVal []int64, k int64) int64 {
	const kvMask int64 = 8191
	slot := int(((k * 2654435761) >> 16) & kvMask)
	for {
		cur := kvKey[slot]
		if cur == -1 {
			return -1
		}
		if cur == k {
			return kvVal[slot]
		}
		slot = (slot + 1) & int(kvMask)
	}
}

func main() {
	const poly int64 = 3988292384
	crcTbl := make([]int64, 256)
	for i := 0; i < 256; i++ {
		c := int64(i)
		for b := 0; b < 8; b++ {
			if (c & 1) != 0 {
				c = poly ^ (c >> 1)
			} else {
				c = c >> 1
			}
		}
		crcTbl[i] = c
	}

	const kvCap = 8192
	kvKey := make([]int64, kvCap)
	kvVal := make([]int64, kvCap)
	for i := 0; i < kvCap; i++ {
		kvKey[i] = -1
	}

	buf := make([]int64, 180000)
	var rng int64 = 999888777
	var lsn int64 = 1
	var replayed int64
	var ck int64

	for seg := int64(0); seg < 40; seg++ {
		blen := 0
		for rec := 0; rec < 3000; rec++ {
			rng = (rng*1103515245 + 12345) & 2147483647
			var op int64 = 1
			if (rng % 6) == 0 {
				op = 2
			}
			rng = (rng*1103515245 + 12345) & 2147483647
			key := rng % 4096
			var vlen int64
			if op == 1 {
				rng = (rng*1103515245 + 12345) & 2147483647
				vlen = 8 + (rng % 32)
			}
			rng = (rng*1103515245 + 12345) & 2147483647
			seed := (rng >> 4) & 255

			recStart := blen
			buf[blen] = 87
			buf[blen+1] = 76
			buf[blen+2] = op
			buf[blen+3] = (lsn ^ key) & 255
			buf[blen+4] = lsn & 255
			buf[blen+5] = (lsn >> 8) & 255
			buf[blen+6] = (lsn >> 16) & 255
			buf[blen+7] = (lsn >> 24) & 255
			buf[blen+8] = key & 255
			buf[blen+9] = (key >> 8) & 255
			buf[blen+10] = (key >> 16) & 255
			buf[blen+11] = (key >> 24) & 255
			buf[blen+12] = vlen & 255
			buf[blen+13] = (vlen >> 8) & 255
			blen += 14
			vl := int(vlen)
			for j := 0; j < vl; j++ {
				buf[blen] = (seed + int64(j)*13 + lsn) & 255
				blen++
			}
			crc := crc32Slice(crcTbl, buf, recStart, 14+vl)
			buf[blen] = crc & 255
			buf[blen+1] = (crc >> 8) & 255
			buf[blen+2] = (crc >> 16) & 255
			buf[blen+3] = (crc >> 24) & 255
			blen += 4
			lsn++
		}

		if (seg % 4) == 3 {
			blen -= 7
		} else if (seg % 5) == 4 {
			buf[blen-2] = buf[blen-2] ^ 1
		}

		pos := 0
		var segRep int64
		var early int64
		for pos < blen {
			if pos+18 > blen {
				early = 1
				break
			}
			if buf[pos] != 87 || buf[pos+1] != 76 {
				early = 1
				break
			}
			op := buf[pos+2]
			if op != 1 && op != 2 {
				early = 1
				break
			}
			vlen := int(buf[pos+12] | (buf[pos+13] << 8))
			if pos+18+vlen > blen {
				early = 1
				break
			}
			stored := buf[pos+14+vlen] | (buf[pos+15+vlen] << 8) | (buf[pos+16+vlen] << 16) | (buf[pos+17+vlen] << 24)
			calc := crc32Slice(crcTbl, buf, pos, 14+vlen)
			if calc != stored {
				early = 1
				break
			}
			key := buf[pos+8] | (buf[pos+9] << 8) | (buf[pos+10] << 16) | (buf[pos+11] << 24)
			if op == 1 {
				var vh int64
				for j := 0; j < vlen; j++ {
					vh = (vh*131 + buf[pos+14+j]) % modV
				}
				kvPut(kvKey, kvVal, key, vh)
			} else {
				kvDel(kvKey, kvVal, key)
			}
			segRep++
			pos += 18 + vlen
		}
		replayed += segRep
		ck = (ck*37 + seg*1009 + segRep*17 + early) % modV
	}

	for k := int64(0); k < 4096; k++ {
		v := kvGet(kvKey, kvVal, k)
		if v >= 0 {
			ck = (ck*31 + k*97 + v) % modV
		}
	}

	fmt.Printf("%d\n%d\n", replayed, ck)
}
