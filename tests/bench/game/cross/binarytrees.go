package main
import ("fmt"; "os"; "strconv")
type Tree struct{ Left, Right *Tree }
func count(t *Tree) int { if t.Left == nil { return 1 }; return 1 + count(t.Left) + count(t.Right) }
func newTree(d int) *Tree {
    if d > 0 { return &Tree{newTree(d - 1), newTree(d - 1)} }
    return &Tree{}
}
func main() {
    maxDepth := 18
    if len(os.Args) > 1 { maxDepth, _ = strconv.Atoi(os.Args[1]) }
    minDepth := 4
    if maxDepth < minDepth+2 { maxDepth = minDepth + 2 }
    stretch := maxDepth + 1
    fmt.Printf("stretch tree of depth %d\t check: %d\n", stretch, count(newTree(stretch)))
    longLived := newTree(maxDepth)
    for depth := minDepth; depth <= maxDepth; depth += 2 {
        iterations := 1 << (maxDepth - depth + minDepth)
        check := 0
        for i := 0; i < iterations; i++ { check += count(newTree(depth)) }
        fmt.Printf("%d\t trees of depth %d\t check: %d\n", iterations, depth, check)
    }
    fmt.Printf("long lived tree of depth %d\t check: %d\n", maxDepth, count(longLived))
}
