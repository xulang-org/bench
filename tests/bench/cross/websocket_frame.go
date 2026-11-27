package main

import "fmt"

const modV int64 = 1000000007

func main() {
	sFin := make([]int64, 80)
	sOp := make([]int64, 80)
	sM0 := make([]int64, 80)
	sM1 := make([]int64, 80)
	sM2 := make([]int64, 80)
	sM3 := make([]int64, 80)
	sLen := make([]int64, 80)
	sSeed := make([]int64, 80)

	var rng int64 = 987654321
	for i := 0; i < 80; i++ {
		tier := i % 4
		rng = (rng*1103515245 + 12345) & 2147483647
		var ln int64
		if tier == 0 {
			ln = 13 + (rng % 90)
		} else if tier == 1 {
			ln = 126 + (rng % 300)
		} else if tier == 2 {
			ln = 500 + (rng % 1500)
		} else {
			ln = 2000 + (rng % 2048)
		}
		var fin int64
		if (i % 5) != 0 {
			fin = 1
		}
		var op int64 = 1
		if (i & 1) == 0 {
			op = 2
		}
		rng = (rng*1103515245 + 12345) & 2147483647
		m0 := (rng >> 8) & 255
		rng = (rng*1103515245 + 12345) & 2147483647
		m1 := (rng >> 8) & 255
		rng = (rng*1103515245 + 12345) & 2147483647
		m2 := (rng >> 8) & 255
		rng = (rng*1103515245 + 12345) & 2147483647
		m3 := (rng >> 8) & 255
		rng = (rng*1103515245 + 12345) & 2147483647
		seed := (rng >> 4) & 255

		sFin[i] = fin
		sOp[i] = op
		sM0[i] = m0
		sM1[i] = m1
		sM2[i] = m2
		sM3[i] = m3
		sLen[i] = ln
		sSeed[i] = seed
	}

	wire := make([]int64, 0, 131072)
	var totalBytes int64
	var ck int64
	for rnd := int64(0); rnd < 180; rnd++ {
		wire = wire[:0]
		for idx := 0; idx < 80; idx++ {
			fin := sFin[idx]
			op := sOp[idx]
			ln := sLen[idx]
			seed := sSeed[idx]
			m0 := (sM0[idx] + rnd) & 255
			m1 := (sM1[idx] + int64(idx)) & 255
			m2 := sM2[idx]
			m3 := sM3[idx]

			wire = append(wire, ((fin&1)<<7)|(op&15))
			if ln <= 125 {
				wire = append(wire, 128|ln)
			} else {
				wire = append(wire, 128|126)
				wire = append(wire, (ln>>8)&255)
				wire = append(wire, ln&255)
			}
			wire = append(wire, m0, m1, m2, m3)

			for j := int64(0); j < ln; j++ {
				pb := (seed + j*17 + rnd*3) & 255
				mk := m0
				switch j & 3 {
				case 1:
					mk = m1
				case 2:
					mk = m2
				case 3:
					mk = m3
				}
				wire = append(wire, pb^mk)
			}
		}

		pos := 0
		wlen := len(wire)
		for pos < wlen {
			b0 := wire[pos]
			b1 := wire[pos+1]
			pos += 2
			fin := (b0 >> 7) & 1
			op := b0 & 15
			masked := (b1 >> 7) & 1
			plen := b1 & 127
			if plen == 126 {
				plen = (wire[pos] << 8) | wire[pos+1]
				pos += 2
			}
			var m0, m1, m2, m3 int64
			if masked != 0 {
				m0, m1, m2, m3 = wire[pos], wire[pos+1], wire[pos+2], wire[pos+3]
				pos += 4
			}
			fh := (fin*17 + op) % modV
			for j := 0; j < int(plen); j++ {
				mk := m0
				switch j & 3 {
				case 1:
					mk = m1
				case 2:
					mk = m2
				case 3:
					mk = m3
				}
				ch := wire[pos+j] ^ mk
				fh = (fh*131 + ch) % modV
			}
			pos += int(plen)
			totalBytes += plen
			ck = (ck*31 + fh) % modV
		}
	}
	fmt.Println(totalBytes)
	fmt.Println(ck)
}
