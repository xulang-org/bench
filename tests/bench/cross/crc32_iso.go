package main

import "fmt"

func main() {
	n := 100000
	data := make([]int64, 0, n)
	seed := int64(123456789)
	i := 0
	for i < n {
		seed = (seed*1103515245 + 12345) & 2147483647
		data = append(data, seed&255)
		i++
	}
	poly := int64(3988292384)
	mask32 := int64(4294967295)
	total := int64(0)
	round := 0
	for round < 20 {
		crc := mask32
		k := 0
		for k < n {
			b := data[k]
			crc = crc ^ b
			bit := 0
			for bit < 8 {
				if (crc & 1) != 0 {
					crc = ((crc >> 1) & 2147483647) ^ poly
				} else {
					crc = (crc >> 1) & 2147483647
				}
				bit++
			}
			k++
		}
		total += crc ^ mask32
		round++
	}
	fmt.Printf("%d\n", total)
}
