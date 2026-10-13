package main
import ("fmt"; "os"; "strconv")
func main() {
    N := 4000
    if len(os.Args) > 1 { N, _ = strconv.Atoi(os.Args[1]) }
    w := (N + 7) / 8 * 8
    pix := make([]byte, w*w/8)
    for y := 0; y < w; y++ {
        Ci := 2.0*float64(y)/float64(w) - 1.0
        for x := 0; x < w; x++ {
            Cr := 2.0*float64(x)/float64(w) - 1.5
            Zr, Zi, Tr, Ti := 0.0, 0.0, 0.0, 0.0
            for i := 0; i < 50 && Tr+Ti <= 4.0; i++ {
                Zi = 2*Zr*Zi + Ci
                Zr = Tr - Ti + Cr
                Tr = Zr * Zr
                Ti = Zi * Zi
            }
            if Tr+Ti <= 4.0 {
                pix[y*(w/8)+(x>>3)] |= 0x80 >> uint(x&7)
            }
        }
    }
    fmt.Printf("P4\n%d %d\n", w, w)
    os.Stdout.Write(pix)
}
