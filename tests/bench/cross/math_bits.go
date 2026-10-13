package main

import (
	"fmt"
	"math/bits"
)

func main() {
	x := uint64(0x123456789abcdef0)
	sum := uint64(0)
	for i := uint64(0); i < 5000000; i++ {
		x = bits.RotateLeft64(x^i, 13)
		sum += uint64(bits.Len64(x))
		sum += uint64(bits.LeadingZeros64(x))
		sum += uint64(bits.TrailingZeros64(x))
		sum += uint64(bits.OnesCount64(x))
		x = bits.ReverseBytes64(x)
		sum ^= bits.Reverse64(x)
	}
	fmt.Printf("%d\n", int64(sum))
}
