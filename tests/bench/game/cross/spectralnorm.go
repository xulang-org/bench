package main
import ("fmt"; "math"; "os"; "strconv")
func evalA(i, j int) int { return (i+j)*(i+j+1)/2 + i + 1 }
func times(v, u []float64) {
    for i := range v { s := 0.0; for j := range u { s += u[j] / float64(evalA(i, j)) }; v[i] = s }
}
func timesT(v, u []float64) {
    for i := range v { s := 0.0; for j := range u { s += u[j] / float64(evalA(j, i)) }; v[i] = s }
}
func AtA(v, u []float64) { x := make([]float64, len(u)); times(x, u); timesT(v, x) }
func main() {
    n := 5500
    if len(os.Args) > 1 { n, _ = strconv.Atoi(os.Args[1]) }
    u := make([]float64, n); v := make([]float64, n)
    for i := range u { u[i] = 1 }
    for k := 0; k < 10; k++ { AtA(v, u); AtA(u, v) }
    var vbv, vv float64
    for i := range u { vbv += u[i] * v[i]; vv += v[i] * v[i] }
    fmt.Printf("%.9f\n", math.Sqrt(vbv/vv))
}
