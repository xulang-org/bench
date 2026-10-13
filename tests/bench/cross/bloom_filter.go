package main

import (
	"fmt"
)

type BloomFilter struct {
	bits []uint64
	mask uint64
}

func newBloom(numBits uint64) *BloomFilter {
	return &BloomFilter{
		bits: make([]uint64, numBits/64),
		mask: numBits - 1,
	}
}

func (bf *BloomFilter) add(val int64) {
	h1 := (val*1103515245 + 12345) & 2147483647
	h2 := (val*1664525 + 1013904223) & 2147483647
	for i := int64(0); i < 4; i++ {
		bit := uint64(h1+i*h2) & bf.mask
		bf.bits[bit>>6] |= (1 << (bit & 63))
	}
}

func (bf *BloomFilter) contains(val int64) bool {
	h1 := (val*1103515245 + 12345) & 2147483647
	h2 := (val*1664525 + 1013904223) & 2147483647
	for i := int64(0); i < 4; i++ {
		bit := uint64(h1+i*h2) & bf.mask
		if (bf.bits[bit>>6] & (1 << (bit & 63))) == 0 {
			return false
		}
	}
	return true
}

func main() {
	bf := newBloom(1048576)
	var seed int64 = 123456789

	for i := 0; i < 200000; i++ {
		seed = (seed*1664525 + 1013904223) % 2147483647
		bf.add(seed)
	}

	var checksum int64 = 0
	for i := 0; i < 2000000; i++ {
		seed = (seed*1664525 + 1013904223) % 2147483647
		if bf.contains(seed) {
			checksum = (checksum*31 + seed) % 1000000007
		}
	}

	fmt.Println(checksum)
}
