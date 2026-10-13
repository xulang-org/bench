package main
import ("fmt"; "os"; "strconv")
func main() {
    n := 12
    if len(os.Args) > 1 { n, _ = strconv.Atoi(os.Args[1]) }
    perm1 := make([]int, n); count := make([]int, n); perm := make([]int, n)
    for i := 0; i < n; i++ { perm1[i] = i }
    maxFlips, checksum, sign, r := 0, 0, 1, n
    for {
        for r != 1 { count[r-1] = r; r-- }
        copy(perm, perm1)
        flips, k := 0, perm[0]
        for k != 0 {
            for i, j := 0, k; i < j; i, j = i+1, j-1 { perm[i], perm[j] = perm[j], perm[i] }
            flips++; k = perm[0]
        }
        if flips > maxFlips { maxFlips = flips }
        checksum += sign * flips; sign = -sign
        for {
            if r == n { fmt.Printf("%d\nPfannkuchen(%d) = %d\n", checksum, n, maxFlips); return }
            p0 := perm1[0]
            for i := 0; i < r; i++ { perm1[i] = perm1[i+1] }
            perm1[r] = p0
            count[r]--; if count[r] > 0 { break }
            r++
        }
    }
}
