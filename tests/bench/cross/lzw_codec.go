package main

import (
	"bytes"
	"compress/lzw"
	"fmt"
	"io"
	"strings"
)

func main() {
	base := "TOBEORNOTTOBEORTOBEORNOT#"
	payload := strings.Repeat(base, 16)
	var total int64 = 0

	for i := 0; i < 2500; i++ {
		var buf bytes.Buffer
		w := lzw.NewWriter(&buf, lzw.LSB, 8)
		w.Write([]byte(payload))
		w.Close()
		enc := buf.Bytes()
		encLen := int64(len(enc))

		r := lzw.NewReader(bytes.NewReader(enc), lzw.LSB, 8)
		dec, err := io.ReadAll(r)
		if err != nil {
			panic(err)
		}
		r.Close()
		total += encLen + int64(len(dec))
		if i == 0 {
			total += int64(dec[0]) + int64(dec[len(dec)-1])
		}
	}
	fmt.Println(total)
}
