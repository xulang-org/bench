package main

import (
	"bytes"
	"fmt"
	"os"
)

func main() {
	payload := bytes.Repeat([]byte{'A'}, 524288)
	sum := int64(0)
	for round := 0; round < 32; round += 1 {
		if err := os.WriteFile("roundtrip.bin", payload, 0o644); err != nil {
			os.Exit(1)
		}
		got, err := os.ReadFile("roundtrip.bin")
		if err != nil || !bytes.Equal(payload, got) {
			os.Exit(1)
		}
		sum += int64(got[0]) + int64(got[len(got)/2]) + int64(got[len(got)-1])
	}
	fmt.Println(sum)
}
