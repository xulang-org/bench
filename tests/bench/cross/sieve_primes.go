package main

import "fmt"

func main() {
	n := 2000000
	isPrime := make([]int64, 0, n+1)
	i := 0
	for i <= n {
		isPrime = append(isPrime, 1)
		i++
	}
	isPrime[0] = 0
	isPrime[1] = 0
	p := 2
	for p*p <= n {
		if isPrime[p] == 1 {
			j := p * p
			for j <= n {
				isPrime[j] = 0
				j += p
			}
		}
		p++
	}
	var count int64 = 0
	var total int64 = 0
	k := 2
	for k <= n {
		if isPrime[k] == 1 {
			count++
			total += int64(k)
		}
		k++
	}
	fmt.Printf("%d\n%d\n", count, total)
}
