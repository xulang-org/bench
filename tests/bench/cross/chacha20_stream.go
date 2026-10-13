package main

import (
	"fmt"
	"math/bits"
)

func qr(s *[16]uint32, a, b, c, d int) {
	s[a] += s[b]
	s[d] = bits.RotateLeft32(s[d]^s[a], 16)
	s[c] += s[d]
	s[b] = bits.RotateLeft32(s[b]^s[c], 12)
	s[a] += s[b]
	s[d] = bits.RotateLeft32(s[d]^s[a], 8)
	s[c] += s[d]
	s[b] = bits.RotateLeft32(s[b]^s[c], 7)
}

func main() {
	var key [8]uint32
	for i := 0; i < 8; i++ {
		key[i] = uint32(i * 16843009)
	}
	nonce0 := uint32(305419896)
	nonce1 := uint32(2596069104)
	nonce2 := uint32(267246505)

	rounds := 30000
	var total_sum uint32
	var s [16]uint32

	for block := 0; block < rounds; block++ {
		s[0] = 1634760805
		s[1] = 857760878
		s[2] = 2036477234
		s[3] = 1797285236
		for k := 0; k < 8; k++ {
			s[4+k] = key[k] + uint32(block)
		}
		s[12] = uint32(block)
		s[13] = nonce0
		s[14] = nonce1
		s[15] = nonce2

		for r := 0; r < 10; r++ {
			qr(&s, 0, 4, 8, 12)
			qr(&s, 1, 5, 9, 13)
			qr(&s, 2, 6, 10, 14)
			qr(&s, 3, 7, 11, 15)
			qr(&s, 0, 5, 10, 15)
			qr(&s, 1, 6, 11, 12)
			qr(&s, 2, 7, 8, 13)
			qr(&s, 3, 4, 9, 14)
		}
		total_sum += s[0] + s[5] + s[10] + s[15]
	}
	fmt.Println(total_sum)
}
