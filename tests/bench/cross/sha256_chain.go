package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strings"
)

func main() {
	var b strings.Builder
	i := 0
	for i < 1024 {
		b.WriteString("The quick brown fox jumps over the lazy dog. 0123456789.")
		i += 1
	}
	body := b.String()
	sum := sha256.Sum256([]byte(body))
	h := hex.EncodeToString(sum[:])
	r := 0
	for r < 4 {
		sum = sha256.Sum256([]byte(h + body))
		h = hex.EncodeToString(sum[:])
		r += 1
	}
	fmt.Println(h)
}
