package main
import ("bufio"; "os"; "strconv")
const width, im, ia, ic = 60, 139968, 3877, 29573
var seed uint32 = 42
type acid struct{ p float64; c byte }
func accumulate(g []acid) { for i := 1; i < len(g); i++ { g[i].p += g[i-1].p } }
func repeatFasta(out *bufio.Writer, alu []byte, count int) {
    pos := 0
    for count > 0 {
        line := width; if count < line { line = count }
        for i := 0; i < line; i++ { out.WriteByte(alu[pos]); pos++; if pos >= len(alu) { pos = 0 } }
        out.WriteByte('\n'); count -= line
    }
}
func randomFasta(out *bufio.Writer, g []acid, count int) {
    for count > 0 {
        line := width; if count < line { line = count }
        for j := 0; j < line; j++ {
            seed = (seed*ia + ic) % im
            r := float64(seed) / float64(im)
            for _, v := range g { if v.p >= r { out.WriteByte(v.c); break } }
        }
        out.WriteByte('\n'); count -= line
    }
}
func main() {
    n := 2500000
    if len(os.Args) > 1 { n, _ = strconv.Atoi(os.Args[1]) }
    out := bufio.NewWriter(os.Stdout); defer out.Flush()
    alu := []byte("GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGGGAGGCCGAGGCGGGCGGATCACCTGAGGTCAGGAGTTCGAGACCAGCCTGGCCAACATGGTGAAACCCCGTCTCTACTAAAAATACAAAAATTAGCCGGGCGTGGTGGCGCGCGCCTGTAATCCCAGCTACTCGGGAGGCTGAGGCAGGAGAATCGCTTGAACCCGGGAGGCGGAGGTTGCAGTGAGCCGAGATCGCGCCACTGCACTCCAGCCTGGGCGACAGAGCGAGACTCCGTCTCAAAAA")
    iub := []acid{{0.27,'a'},{0.12,'c'},{0.12,'g'},{0.27,'t'},{0.02,'B'},{0.02,'D'},{0.02,'H'},{0.02,'K'},{0.02,'M'},{0.02,'N'},{0.02,'R'},{0.02,'S'},{0.02,'V'},{0.02,'W'},{0.02,'Y'}}
    hs := []acid{{0.3029549426680,'a'},{0.1979883004921,'c'},{0.1975473066391,'g'},{0.3015094502008,'t'}}
    accumulate(iub); accumulate(hs)
    out.WriteString(">ONE Homo sapiens alu\n"); repeatFasta(out, alu, 2*n)
    out.WriteString(">TWO IUB ambiguity codes\n"); randomFasta(out, iub, 3*n)
    out.WriteString(">THREE Homo sapiens frequency\n"); randomFasta(out, hs, 5*n)
}
