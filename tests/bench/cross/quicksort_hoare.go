package main

import (
	"fmt"
)

func qsort(a []int64, low, high int) {
	if low >= high {
		return
	}
	pivot := a[(low+high)/2]
	i := low
	j := high
	for i <= j {
		for a[i] < pivot {
			i++
		}
		for a[j] > pivot {
			j--
		}
		if i <= j {
			a[i], a[j] = a[j], a[i]
			i++
			j--
		}
	}
	if low < j {
		qsort(a, low, j)
	}
	if i < high {
		qsort(a, i, high)
	}
}

func main() {
	var checksum int64 = 0
	arr := make([]int64, 100000)

	for round := 0; round < 5; round++ {
		seed := int64(123456789 + round*1013904223)
		for k := 0; k < 100000; k++ {
			seed = (seed*1664525 + 1013904223) % 2147483647
			arr[k] = seed
		}
		qsort(arr, 0, len(arr)-1)
		for i := 0; i < len(arr); i++ {
			checksum = (checksum*31 + arr[i]) % 1000000007
		}
	}

	fmt.Println(checksum)
}
