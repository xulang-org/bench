fn main() {
    let n: usize = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(4000);
    let w = (n + 7) / 8 * 8;
    let mut pix = vec![0u8; w * w / 8];
    for y in 0..w {
        let ci = 2.0 * (y as f64) / (w as f64) - 1.0;
        for x in 0..w {
            let cr = 2.0 * (x as f64) / (w as f64) - 1.5;
            let (mut zr, mut zi, mut tr, mut ti) = (0.0, 0.0, 0.0, 0.0);
            let mut i = 0;
            while i < 50 && tr + ti <= 4.0 {
                zi = 2.0 * zr * zi + ci;
                zr = tr - ti + cr;
                tr = zr * zr;
                ti = zi * zi;
                i += 1;
            }
            if tr + ti <= 4.0 {
                pix[y * (w / 8) + (x >> 3)] |= 0x80 >> (x & 7);
            }
        }
    }
    print!("P4\n{w} {w}\n");
    use std::io::Write;
    let _ = std::io::stdout().write_all(&pix);
}
