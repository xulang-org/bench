fn main() {
    let mut x: u64 = 0x123456789abcdef0;
    let mut sum: u64 = 0;
    for i in 0..5000000u64 {
        x = (x ^ i).rotate_left(13);
        let lz = x.leading_zeros() as u64;
        sum = sum.wrapping_add(64 - lz);
        sum = sum.wrapping_add(lz);
        sum = sum.wrapping_add(x.trailing_zeros() as u64);
        sum = sum.wrapping_add(x.count_ones() as u64);
        x = x.swap_bytes();
        sum ^= x.reverse_bits();
    }
    println!("{}", sum as i64);
}
