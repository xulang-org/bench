package main

import "fmt"

func main() {
	var a [256]int64
	var b [256]int64
	var dp [512]int64

	var rng int64 = 987654321
	var sumLev int64
	var ckLev int64
	for p := 0; p < 400; p++ {
		rng = (rng*1103515245 + 12345) & 2147483647
		la := 120 + (rng % 100)
		rng = (rng*1103515245 + 12345) & 2147483647
		lb := 120 + (rng % 100)
		for i := int64(0); i < la; i++ {
			rng = (rng*1103515245 + 12345) & 2147483647
			a[i] = 97 + ((rng >> 16) & 7)
		}
		for i := int64(0); i < lb; i++ {
			rng = (rng*1103515245 + 12345) & 2147483647
			if i < la && (rng%5) == 0 {
				b[i] = a[i]
			} else {
				b[i] = 97 + ((rng >> 16) & 7)
			}
		}

		for j := int64(0); j <= lb; j++ {
			dp[j] = j
		}
		for i := int64(1); i <= la; i++ {
			curOff := (i & 1) * 256
			prevOff := 256 - curOff
			dp[curOff] = i
			ai := a[i-1]
			for j := int64(1); j <= lb; j++ {
				var cost int64 = 1
				if ai == b[j-1] {
					cost = 0
				}
				d1 := dp[prevOff+j] + 1
				d2 := dp[curOff+j-1] + 1
				d3 := dp[prevOff+j-1] + cost
				best := d1
				if d2 < best {
					best = d2
				}
				if d3 < best {
					best = d3
				}
				dp[curOff+j] = best
			}
		}
		d := dp[(la&1)*256+lb]
		sumLev += d
		ckLev = (ckLev*1000003 + d) % 1000000007
	}
	fmt.Println(sumLev)
	fmt.Println(ckLev)
}
