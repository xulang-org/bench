const WIDTH: i32 = 60; const IM: u32 = 139968; const IA: u32 = 3877; const IC: u32 = 29573;
struct Acid { p: f64, c: u8 }
fn accumulate(g: &mut [Acid]) { for i in 1..g.len() { g[i].p += g[i-1].p; } }
fn repeat_fasta(alu: &[u8], mut count: i32) {
    let mut pos = 0usize;
    while count > 0 {
        let line = if count < WIDTH { count } else { WIDTH };
        for _ in 0..line {
            print!("{}", alu[pos] as char); pos += 1; if pos >= alu.len() { pos = 0; }
        }
        println!(); count -= line;
    }
}
fn random_fasta(g: &[Acid], mut count: i32, seed: &mut u32) {
    while count > 0 {
        let line = if count < WIDTH { count } else { WIDTH };
        for _ in 0..line {
            *seed = (*seed * IA + IC) % IM;
            let r = (*seed as f64) / (IM as f64);
            for a in g { if a.p >= r { print!("{}", a.c as char); break; } }
        }
        println!(); count -= line;
    }
}
fn main() {
    let n: i32 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(2_500_000);
    let alu = b"GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGGGAGGCCGAGGCGGGCGGATCACCTGAGGTCAGGAGTTCGAGACCAGCCTGGCCAACATGGTGAAACCCCGTCTCTACTAAAAATACAAAAATTAGCCGGGCGTGGTGGCGCGCGCCTGTAATCCCAGCTACTCGGGAGGCTGAGGCAGGAGAATCGCTTGAACCCGGGAGGCGGAGGTTGCAGTGAGCCGAGATCGCGCCACTGCACTCCAGCCTGGGCGACAGAGCGAGACTCCGTCTCAAAAA";
    let mut iub = [
        Acid{p:0.27,c:b'a'},Acid{p:0.12,c:b'c'},Acid{p:0.12,c:b'g'},Acid{p:0.27,c:b't'},
        Acid{p:0.02,c:b'B'},Acid{p:0.02,c:b'D'},Acid{p:0.02,c:b'H'},Acid{p:0.02,c:b'K'},
        Acid{p:0.02,c:b'M'},Acid{p:0.02,c:b'N'},Acid{p:0.02,c:b'R'},Acid{p:0.02,c:b'S'},
        Acid{p:0.02,c:b'V'},Acid{p:0.02,c:b'W'},Acid{p:0.02,c:b'Y'},
    ];
    let mut hs = [
        Acid{p:0.3029549426680,c:b'a'},Acid{p:0.1979883004921,c:b'c'},
        Acid{p:0.1975473066391,c:b'g'},Acid{p:0.3015094502008,c:b't'},
    ];
    accumulate(&mut iub); accumulate(&mut hs);
    let mut seed = 42u32;
    println!(">ONE Homo sapiens alu"); repeat_fasta(alu, 2*n);
    println!(">TWO IUB ambiguity codes"); random_fasta(&iub, 3*n, &mut seed);
    println!(">THREE Homo sapiens frequency"); random_fasta(&hs, 5*n, &mut seed);
}
