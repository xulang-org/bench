package main

import (
	"fmt"
	"strings"
)

func main() {
	pool := make([]string, 0, 32)
	for si := int64(0); si < 32; si++ {
		n := 8 + si%24
		src := make([]byte, int(n))
		for j := int64(0); j < n; j++ {
			src[j] = byte(97 + (j+si)%3)
		}
		pool = append(pool, string(src))
	}
	state, total, i := int64(1), int64(0), int64(0)
	for i < 1000000 {
		state = (state*1103515245 + 12345) & 2147483647
		idx := (state >> 16) & 31
		needle := "a"
		if ((state >> 8) & 1) == 1 {
			needle = "b"
		}
		total += int64(strings.Count(pool[idx], needle))
		i++
	}
	fmt.Println(total)
}
