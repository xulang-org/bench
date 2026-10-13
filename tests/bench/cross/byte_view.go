package main

import (
	"fmt"
	"strings"
)

func main() {
	var sb strings.Builder
	sb.Grow(100000)
	i := int64(0)
	for i < 10000 {
		sb.WriteString("0123456789")
		i += 1
	}
	s := sb.String()
	hits := int64(0)
	k := int64(0)
	for k < 20 {
		if strings.IndexByte(s, '9') >= 0 {
			hits += 1
		}
		if strings.Index(s, "89012") >= 0 {
			hits += 1
		}
		k += 1
	}
	fmt.Printf("%d\n%d\n", hits, len(s))
}
