package main

import (
    "fmt"
    "math/bits"
)

func main() {
    var x int64 = 0x123456789abcdef0
    var sum int64
    for i := int64(0); i < 10000000; i++ {
        x = int64(bits.ReverseBytes64(uint64(x ^ i)))
        sum ^= x
    }
    fmt.Println(x)
    fmt.Println(sum)
}
