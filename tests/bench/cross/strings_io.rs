fn count_char(s: &str, c: char) -> usize {
    s.chars().filter(|&ch| ch == c).count()
}

fn main() {
    let seed = "alpha,beta,gamma,delta;omega,phi,chi;lambda,mu,nu";
    let base = seed.repeat(384);
    let mut total: i64 = 0;
    let mut i = 0;
    while i < 2500 {
        let s = base.replace('a', "A");
        total += s.len() as i64;
        let parts: Vec<&str> = s.split(';').collect();
        total += parts.len() as i64;
        let mut j = 0;
        while j < parts.len() {
            let p = parts[j];
            total += p.len() as i64;
            if p.starts_with('A') {
                total += 1;
            }
            total += count_char(p, 'a') as i64;
            j += 1;
        }
        let line = parts.join("|");
        total += line.len() as i64;

        let trimmed = line.trim();
        let bytes = trimmed.as_bytes();
        let read_n = bytes.len().min(256);
        total += read_n as i64;
        let rem = bytes.len() - read_n;
        if rem > 0 {
            total += rem as i64;
        }
        i += 1;
    }
    println!("{}", total);
}
