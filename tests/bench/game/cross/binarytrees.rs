struct Tree { left: Option<Box<Tree>>, right: Option<Box<Tree>> }
fn new_tree(d: i32) -> Tree {
    if d > 0 { Tree{ left: Some(Box::new(new_tree(d-1))), right: Some(Box::new(new_tree(d-1))) } }
    else { Tree{ left: None, right: None } }
}
fn count(t: &Tree) -> i32 {
    match &t.left {
        None => 1,
        Some(l) => 1 + count(l) + count(t.right.as_ref().unwrap()),
    }
}
fn main() {
    let mut max_depth: i32 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(18);
    let min_depth = 4;
    if max_depth < min_depth + 2 { max_depth = min_depth + 2; }
    let stretch = max_depth + 1;
    println!("stretch tree of depth {}\t check: {}", stretch, count(&new_tree(stretch)));
    let long_lived = new_tree(max_depth);
    let mut depth = min_depth;
    while depth <= max_depth {
        let iterations = 1 << (max_depth - depth + min_depth);
        let mut check = 0;
        for _ in 0..iterations { check += count(&new_tree(depth)); }
        println!("{iterations}\t trees of depth {depth}\t check: {check}");
        depth += 2;
    }
    println!("long lived tree of depth {}\t check: {}", max_depth, count(&long_lived));
}
