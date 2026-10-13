package main

import (
	"fmt"
	"strings"
)

func tokenize(src string) (int, int64) {
	n := len(src)
	pos := 0
	count := 0
	var chk int64 = 0
	for pos < n {
		c := src[pos]
		if c == 32 || c == 9 || c == 10 || c == 13 {
			pos++
			continue
		}
		var tType, tLen int64
		if c == 123 {
			tType = 1; tLen = 1; pos++
		} else if c == 125 {
			tType = 2; tLen = 1; pos++
		} else if c == 91 {
			tType = 3; tLen = 1; pos++
		} else if c == 93 {
			tType = 4; tLen = 1; pos++
		} else if c == 58 {
			tType = 5; tLen = 1; pos++
		} else if c == 44 {
			tType = 6; tLen = 1; pos++
		} else if c == 34 {
			tType = 7
			start := pos
			pos++
			for pos < n {
				ch := src[pos]
				if ch == 92 {
					pos += 2
				} else if ch == 34 {
					pos++
					break
				} else {
					pos++
				}
			}
			tLen = int64(pos - start)
		} else if c == 45 || (c >= 48 && c <= 57) {
			tType = 8
			start := pos
			if c == 45 {
				pos++
			}
			for pos < n && (src[pos] >= 48 && src[pos] <= 57) {
				pos++
			}
			if pos < n && src[pos] == 46 {
				pos++
				for pos < n && (src[pos] >= 48 && src[pos] <= 57) {
					pos++
				}
			}
			tLen = int64(pos - start)
		} else if c == 116 {
			tType = 9; tLen = 4; pos += 4
		} else if c == 102 {
			tType = 10; tLen = 5; pos += 5
		} else if c == 110 {
			tType = 11; tLen = 4; pos += 4
		} else {
			pos++
			continue
		}
		count++
		chk = (chk*37 + tType*101 + tLen) % 1000000007
	}
	return count, chk
}

func main() {
	base := "{\"project\":\"Xu\",\"version\":1.0,\"active\":true,\"count\":100,\"flag\":false,\"note\":null,\"data\":[1,2,-3,40]}"
	full := strings.Repeat(base, 10)
	var total int64 = 0
	for r := 0; r < 1000; r++ {
		_, c := tokenize(full)
		total = (total*31 + c) % 1000000007
	}
	fmt.Println(total)
}
