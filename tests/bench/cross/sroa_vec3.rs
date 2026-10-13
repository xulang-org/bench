struct Vec3 {
    x: f64,
    y: f64,
    z: f64,
}

fn main() {
    let mut v: Vec<Vec3> = Vec::new();
    let mut i: i64 = 0;
    while i < 256 {
        v.push(Vec3 {
            x: (i & 7) as f64,
            y: ((i * 3) & 7) as f64,
            z: ((i * 5) & 7) as f64,
        });
        i += 1;
    }
    let mut acc = 0.0;
    let mut t: i64 = 0;
    while t < 40_000 {
        i = 0;
        while i < 256 {
            let p = &v[i as usize];
            acc += p.x * p.x + p.y * p.y + p.z * p.z;
            i += 1;
        }
        t += 1;
    }
    println!("{}", acc as i64);
}
