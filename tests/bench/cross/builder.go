package main

import (
	"fmt"
	"strings"
)

func main() {
	var b strings.Builder
	b.Grow(64)
	i := int64(0)
	for i < 100000 {
		b.WriteByte(byte(48 + (i % 10)))
		i += 1
	}
	t := b.String()
	c := int64(0)
	j := int64(0)
	n := int64(len(t))
	for j < n {
		c += int64(t[j])
		j += 1
	}
	fmt.Printf("%d\n%d\n", c, n)
}
