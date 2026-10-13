fn main() {
    let seed = "alpha,beta,gamma,delta;omega,phi,chi;lambda,mu,nu";
    let mut total: i64 = 0;
    for i in 0..25000 {
        let out = seed.repeat(384 + (i & 1));
        std::hint::black_box(&out);
        total += out.len() as i64 + out.as_bytes()[100] as i64;
    }
    println!("{}", total);
}
