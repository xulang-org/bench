package main

import (
	"crypto/md5"
	"encoding/hex"
	"fmt"
)

func main() {
	h := "The quick brown fox jumps over the lazy dog"
	for i := 0; i < 100000; i++ {
		sum := md5.Sum([]byte(h))
		h = hex.EncodeToString(sum[:])
	}
	fmt.Println(h)
}
