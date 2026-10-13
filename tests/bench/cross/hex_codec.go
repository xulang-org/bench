package main

import (
	"encoding/hex"
	"fmt"
	"strings"
)

func main() {
	base := "The quick brown fox jumps over the lazy dog 0123456789 ABCDEFGHIJKLMNOP"
	payload := strings.Repeat(base, 8)
	var total int64 = 0

	for i := 0; i < 25000; i++ {
		enc := hex.EncodeToString([]byte(payload))
		encLen := int64(len(enc))
		dec, err := hex.DecodeString(enc)
		if err != nil {
			panic(err)
		}
		total += encLen + int64(len(dec))
		if i == 0 {
			total += int64(dec[0]) + int64(dec[len(dec)-1])
		}
	}

	fmt.Println(total)
}
