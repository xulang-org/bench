// Osprey (MIT): benchmarks/cases/binarytrees; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
final class Tree {
    let left, right: Tree?
    init(_ left: Tree?, _ right: Tree?) { self.left = left; self.right = right }
}

func makeTree(_ depth: Int64) -> Tree {
    if depth == 0 { return Tree(nil, nil) }
    let left = makeTree(depth - 1)
    let right = makeTree(depth - 1)
    return Tree(left, right)
}

func check(_ t: Tree?) -> Int64 {
    guard let t = t else { return 0 }
    return 1 + check(t.left) + check(t.right)
}

func main() {
    var result: Int64 = 0
    var i: Int64 = 0
    while i < 1200 {
        let tree = makeTree(13)
        result += check(tree)
        i += 1
    }
    print(result)
}

main()
