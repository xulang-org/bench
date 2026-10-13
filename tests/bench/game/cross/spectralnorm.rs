fn eval_a(i: usize, j: usize) -> f64 { ((i+j)*(i+j+1)/2 + i + 1) as f64 }
fn times(v: &mut [f64], u: &[f64]) {
    let n = v.len();
    for i in 0..n { let mut s=0.; for j in 0..n { s += u[j]/eval_a(i,j); } v[i]=s; }
}
fn times_t(v: &mut [f64], u: &[f64]) {
    let n = v.len();
    for i in 0..n { let mut s=0.; for j in 0..n { s += u[j]/eval_a(j,i); } v[i]=s; }
}
fn ata(v: &mut [f64], u: &[f64]) {
    let mut x = vec![0.; u.len()]; times(&mut x, u); times_t(v, &x);
}
fn main() {
    let n: usize = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(5500);
    let mut u = vec![1.; n]; let mut v = vec![0.; n];
    for _ in 0..10 { ata(&mut v, &u); ata(&mut u, &v); }
    let mut vbv=0.; let mut vv=0.;
    for i in 0..n { vbv += u[i]*v[i]; vv += v[i]*v[i]; }
    println!("{:.9}", (vbv/vv).sqrt());
}
