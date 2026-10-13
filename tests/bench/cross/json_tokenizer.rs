fn tokenize(src: &[u8]) -> (usize, i64) {
    let mut pos = 0;
    let n = src.len();
    let mut count = 0;
    let mut chk = 0i64;
    while pos < n {
        let c = src[pos];
        if c == 32 || c == 9 || c == 10 || c == 13 {
            pos += 1;
            continue;
        }
        let t_type: i64;
        let t_len: i64;
        if c == 123 {
            t_type = 1; t_len = 1; pos += 1;
        } else if c == 125 {
            t_type = 2; t_len = 1; pos += 1;
        } else if c == 91 {
            t_type = 3; t_len = 1; pos += 1;
        } else if c == 93 {
            t_type = 4; t_len = 1; pos += 1;
        } else if c == 58 {
            t_type = 5; t_len = 1; pos += 1;
        } else if c == 44 {
            t_type = 6; t_len = 1; pos += 1;
        } else if c == 34 {
            t_type = 7;
            let start = pos;
            pos += 1;
            while pos < n {
                let ch = src[pos];
                if ch == 92 {
                    pos += 2;
                } else if ch == 34 {
                    pos += 1;
                    break;
                } else {
                    pos += 1;
                }
            }
            t_len = (pos - start) as i64;
        } else if c == 45 || (c >= 48 && c <= 57) {
            t_type = 8;
            let start = pos;
            if c == 45 { pos += 1; }
            while pos < n && (src[pos] >= 48 && src[pos] <= 57) {
                pos += 1;
            }
            if pos < n && src[pos] == 46 {
                pos += 1;
                while pos < n && (src[pos] >= 48 && src[pos] <= 57) {
                    pos += 1;
                }
            }
            t_len = (pos - start) as i64;
        } else if c == 116 {
            t_type = 9; t_len = 4; pos += 4;
        } else if c == 102 {
            t_type = 10; t_len = 5; pos += 5;
        } else if c == 110 {
            t_type = 11; t_len = 4; pos += 4;
        } else {
            pos += 1;
            continue;
        }
        count += 1;
        chk = (chk * 37 + t_type * 101 + t_len) % 1000000007;
    }
    (count, chk)
}

fn main() {
    let base = "{\"project\":\"Xu\",\"version\":1.0,\"active\":true,\"count\":100,\"flag\":false,\"note\":null,\"data\":[1,2,-3,40]}";
    let full = base.repeat(10);
    let bytes = full.as_bytes();
    let mut total = 0i64;
    for _ in 0..1000 {
        let (_, c) = tokenize(bytes);
        total = (total * 31 + c) % 1000000007;
    }
    println!("{}", total);
}
