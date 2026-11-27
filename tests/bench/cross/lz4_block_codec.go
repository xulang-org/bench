package main

import "fmt"

const modV int64 = 1000000007

func lz4Compress(blocks []int64, srcOff, n int, ht []int, comp []int64) int {
	for i := 0; i < 4096; i++ {
		ht[i] = -1
	}
	op := 0
	ip := 0
	anchor := 0
	limit := n - 12
	mflimit := n - 5
	for ip < limit {
		p := srcOff + ip
		seq := blocks[p] | (blocks[p+1] << 8) | (blocks[p+2] << 16) | (blocks[p+3] << 24)
		h := int(((seq * 73244475) >> 18) & 4095)
		ref := ht[h]
		ht[h] = ip
		if ref >= 0 && (ip-ref) <= 65535 {
			rp := srcOff + ref
			if blocks[rp] == blocks[p] && blocks[rp+1] == blocks[p+1] && blocks[rp+2] == blocks[p+2] && blocks[rp+3] == blocks[p+3] {
				mlen := 4
				for ip+mlen < mflimit && blocks[rp+mlen] == blocks[p+mlen] {
					mlen++
				}
				litLen := ip - anchor
				mExtra := mlen - 4
				tokLit := litLen
				if tokLit >= 15 {
					tokLit = 15
				}
				tokM := mExtra
				if tokM >= 15 {
					tokM = 15
				}
				comp[op] = int64((tokLit << 4) | tokM)
				op++
				if litLen >= 15 {
					rem := litLen - 15
					for rem >= 255 {
						comp[op] = 255
						op++
						rem -= 255
					}
					comp[op] = int64(rem)
					op++
				}
				for j := 0; j < litLen; j++ {
					comp[op] = blocks[srcOff+anchor+j]
					op++
				}
				off := ip - ref
				comp[op] = int64(off & 255)
				comp[op+1] = int64((off >> 8) & 255)
				op += 2
				if mExtra >= 15 {
					rem := mExtra - 15
					for rem >= 255 {
						comp[op] = 255
						op++
						rem -= 255
					}
					comp[op] = int64(rem)
					op++
				}
				ip += mlen
				anchor = ip
				continue
			}
		}
		ip++
	}
	litLen := n - anchor
	tokLit := litLen
	if tokLit >= 15 {
		tokLit = 15
	}
	comp[op] = int64(tokLit << 4)
	op++
	if litLen >= 15 {
		rem := litLen - 15
		for rem >= 255 {
			comp[op] = 255
			op++
			rem -= 255
		}
		comp[op] = int64(rem)
		op++
	}
	for j := 0; j < litLen; j++ {
		comp[op] = blocks[srcOff+anchor+j]
		op++
	}
	return op
}

func lz4Decompress(comp []int64, clen int, decomp []int64) {
	ip := 0
	op := 0
	for ip < clen {
		tok := int(comp[ip])
		ip++
		litLen := tok >> 4
		if litLen == 15 {
			for {
				b := int(comp[ip])
				ip++
				litLen += b
				if b != 255 {
					break
				}
			}
		}
		for j := 0; j < litLen; j++ {
			decomp[op] = comp[ip]
			op++
			ip++
		}
		if ip >= clen {
			break
		}
		off := int(comp[ip] | (comp[ip+1] << 8))
		ip += 2
		mlen := (tok & 15) + 4
		if (tok & 15) == 15 {
			for {
				b := int(comp[ip])
				ip++
				mlen += b
				if b != 255 {
					break
				}
			}
		}
		mp := op - off
		for j := 0; j < mlen; j++ {
			decomp[op] = decomp[mp+j]
			op++
		}
	}
}

func main() {
	const blkLen = 32768
	var rng int64 = 135724680
	phrases := []string{
		"{\"level\":\"INFO\",\"service\":\"storage-node\",\"msg\":\"compaction_ok\",\"ms\":",
		"{\"level\":\"WARN\",\"service\":\"rpc-gateway\",\"msg\":\"retry_backoff\",\"ms\":",
		"SELECT region, category, SUM(amount) FROM orders WHERE status = 1; ",
		"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
		"GET /api/v1/users/profile HTTP/1.1\r\nHost: api.xulang.org\r\n\r\n",
		"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
	}

	blocks := make([]int64, 0, 24*blkLen)
	for bi := 0; bi < 24; bi++ {
		src := make([]int64, 0, blkLen+128)
		for len(src) < blkLen {
			rng = (rng*1103515245 + 12345) & 2147483647
			k := int(rng % 10)
			if k < 6 {
				ps := phrases[k]
				for i := 0; i < len(ps); i++ {
					src = append(src, int64(ps[i]))
				}
				rng = (rng*1103515245 + 12345) & 2147483647
				v := rng % 1000
				src = append(src, 48+(v/100))
				src = append(src, 48+((v/10)%10))
				src = append(src, 48+(v%10))
				src = append(src, 10)
			} else if k < 8 {
				rng = (rng*1103515245 + 12345) & 2147483647
				ch := 65 + (rng % 26)
				rng = (rng*1103515245 + 12345) & 2147483647
				rl := int(12 + (rng % 48))
				for j := 0; j < rl; j++ {
					src = append(src, ch)
				}
			} else {
				rng = (rng*1103515245 + 12345) & 2147483647
				rl := int(8 + (rng % 24))
				for j := 0; j < rl; j++ {
					rng = (rng*1103515245 + 12345) & 2147483647
					src = append(src, 32+(rng%95))
				}
			}
		}
		blocks = append(blocks, src[:blkLen]...)
	}

	ht := make([]int, 4096)
	comp := make([]int64, blkLen+4096)
	decomp := make([]int64, blkLen)

	var totalComp int64
	var ck int64
	for rnd := 0; rnd < 4; rnd++ {
		for bi := 0; bi < 24; bi++ {
			clen := lz4Compress(blocks, bi*blkLen, blkLen, ht, comp)
			lz4Decompress(comp, clen, decomp)
			h := int64(clen)
			for i := 0; i < blkLen; i++ {
				h = (h*131 + decomp[i]) % modV
			}
			totalComp += int64(clen)
			ck = (ck*31 + h) % modV
		}
	}

	fmt.Printf("%d\n%d\n", totalComp, ck)
}
