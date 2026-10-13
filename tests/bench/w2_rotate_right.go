package main

import (
    "fmt"
    "math/bits"
)

func main() {
    x := uint64(0x123456789abcdef0)
    var checksum uint64
    for i := uint64(0); i < 10000000; i++ {
        x = bits.RotateLeft64(x ^ i, -int(i & 63))
        checksum ^= x
    }
    fmt.Println(int64(x))
    fmt.Println(int64(checksum))
}
