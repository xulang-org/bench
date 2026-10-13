use std::cmp::Reverse;
use std::collections::BinaryHeap;

fn main() {
    let mut h = BinaryHeap::new();
    let mut seed: i64 = 123456789;
    let mut checksum: i64 = 0;

    for _ in 0..200000 {
        seed = (seed * 1664525 + 1013904223) % 2147483647;
        h.push(Reverse(seed));
    }

    for _ in 0..100000 {
        if let Some(Reverse(v)) = h.pop() {
            checksum = (checksum * 31 + v) % 1000000007;
        }
    }

    for _ in 0..100000 {
        seed = (seed * 1664525 + 1013904223) % 2147483647;
        h.push(Reverse(seed));
    }

    while let Some(Reverse(v)) = h.pop() {
        checksum = (checksum * 31 + v) % 1000000007;
    }

    println!("{}", checksum);
}
