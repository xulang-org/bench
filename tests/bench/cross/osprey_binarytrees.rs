// Osprey (MIT): benchmarks/cases/binarytrees; deterministic original workload.
// https://github.com/Nimblesite/osprey ; see tests/bench/osprey/README.md.
enum Tree { Leaf, Node(Box<Tree>, Box<Tree>) }

fn make(depth: i64) -> Tree {
    if depth == 0 { return Tree::Node(Box::new(Tree::Leaf), Box::new(Tree::Leaf)); }
    let left = Box::new(make(depth - 1));
    let right = Box::new(make(depth - 1));
    Tree::Node(left, right)
}

fn check(t: &Tree) -> i64 {
    match t {
        Tree::Leaf => 0,
        Tree::Node(left, right) => 1 + check(left) + check(right),
    }
}

fn main() {
    let mut result: i64 = 0;
    let mut i: i64 = 0;
    while i < 1200 {
        let tree = make(13);
        result += check(&tree);
        i += 1;
    }
    println!("{}", result);
}
