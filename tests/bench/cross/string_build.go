package main

import (
	"fmt"
	"strings"
)

func main() {
	var b strings.Builder
	i := 0
	for i < 100000 {
		b.WriteString("0123456789")
		i += 1
	}
	s := b.String()
	c := 0
	j := 0
	for j < len(s) {
		c += int(s[j])
		j += 1
	}
	fmt.Println(c)
	fmt.Println(len(s))
}
