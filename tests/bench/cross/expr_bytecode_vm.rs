const MOD_V: i64 = 1000000007;
const MASK30: i64 = 1073741823;
const BASE30: i64 = 1073741824;

struct Compiler {
    tk: Vec<usize>,
    tv: Vec<i64>,
    pos: usize,
    code: Vec<usize>,
    imm: Vec<i64>,
}

impl Compiler {
    fn new() -> Self {
        Self {
            tk: Vec::new(),
            tv: Vec::new(),
            pos: 0,
            code: Vec::new(),
            imm: Vec::new(),
        }
    }

    fn lex(&mut self, s: &[u8]) {
        self.tk.clear();
        self.tv.clear();
        let mut i = 0usize;
        let n = s.len();
        while i < n {
            let b = s[i];
            if b == 32 {
                i += 1;
            } else if b >= 48 && b <= 57 {
                let mut v: i64 = 0;
                while i < n && s[i] >= 48 && s[i] <= 57 {
                    v = (v * 10 + (s[i] - 48) as i64) & MASK30;
                    i += 1;
                }
                self.tk.push(1);
                self.tv.push(v);
            } else {
                let kind = match b {
                    120 => 2,
                    121 => 3,
                    122 => 4,
                    43 => 5,
                    45 => 6,
                    42 => 7,
                    47 => 8,
                    37 => 9,
                    38 => 10,
                    124 => 11,
                    94 => 12,
                    126 => 13,
                    40 => 14,
                    _ => 15,
                };
                self.tk.push(kind);
                self.tv.push(0);
                i += 1;
            }
        }
        self.tk.push(0);
        self.tv.push(0);
        self.pos = 0;
        self.code.clear();
        self.imm.clear();
    }

    fn parse_prim(&mut self) {
        let t = self.tk[self.pos];
        if t == 1 {
            self.code.push(1);
            self.imm.push(self.tv[self.pos]);
            self.pos += 1;
        } else if t == 2 || t == 3 || t == 4 {
            self.code.push(t);
            self.imm.push(0);
            self.pos += 1;
        } else {
            self.pos += 1;
            self.parse_or();
            self.pos += 1;
        }
    }

    fn parse_unary(&mut self) {
        let t = self.tk[self.pos];
        if t == 6 {
            self.pos += 1;
            self.parse_unary();
            self.code.push(13);
            self.imm.push(0);
        } else if t == 13 {
            self.pos += 1;
            self.parse_unary();
            self.code.push(14);
            self.imm.push(0);
        } else {
            self.parse_prim();
        }
    }

    fn parse_mul(&mut self) {
        self.parse_unary();
        while self.tk[self.pos] == 7 || self.tk[self.pos] == 8 || self.tk[self.pos] == 9 {
            let op = self.tk[self.pos];
            self.pos += 1;
            self.parse_unary();
            self.code.push(op);
            self.imm.push(0);
        }
    }

    fn parse_add(&mut self) {
        self.parse_mul();
        while self.tk[self.pos] == 5 || self.tk[self.pos] == 6 {
            let op = self.tk[self.pos];
            self.pos += 1;
            self.parse_mul();
            self.code.push(op);
            self.imm.push(0);
        }
    }

    fn parse_and(&mut self) {
        self.parse_add();
        while self.tk[self.pos] == 10 {
            self.pos += 1;
            self.parse_add();
            self.code.push(10);
            self.imm.push(0);
        }
    }

    fn parse_xor(&mut self) {
        self.parse_and();
        while self.tk[self.pos] == 12 {
            self.pos += 1;
            self.parse_and();
            self.code.push(12);
            self.imm.push(0);
        }
    }

    fn parse_or(&mut self) {
        self.parse_xor();
        while self.tk[self.pos] == 11 {
            self.pos += 1;
            self.parse_xor();
            self.code.push(11);
            self.imm.push(0);
        }
    }
}

fn main() {
    let exprs: [&[u8]; 16] = [
        b"((x + y) * (z + 7) - (x ^ y)) / ((z & 15) + 1) + (x % 97)",
        b"(~x & 65535) + ((y * 13 + z) ^ (x + y + z)) - (y / 3)",
        b"((x * 3 + y * 5 + z * 7) ^ (x * 11 - y)) + ((z | 255) & (x + 1023))",
        b"-(x - y) + (z * (x & 255) + (y % 31)) ^ (~z & 4095)",
        b"(((x + 17) * (y + 29)) % 65521) + ((z ^ (x + y)) / ((x & 7) + 1))",
        b"((x | y) & (y | z) & (z | x)) + ((x ^ y ^ z) * 19) - (z % 17)",
        b"(x + (y + (z + (x * 3 + (y * 5 - z))))) & 1048575",
        b"((x / 5 + y / 7 + z / 11) * (x % 13 + y % 17 + 1)) ^ (x + z)",
        b"((~x & 1023) * (~y & 1023) + (~z & 1023)) % 1000003",
        b"(((x ^ 12345) + (y ^ 6789)) * 7) / ((z % 23) + 2) + (y & 511)",
        b"(x * (y & 63) - y * (z & 63) + z * (x & 63)) ^ ((x + y) | z)",
        b"((x + y + z) * (x + y + z)) / (x % 29 + y % 31 + 3) + (~(x & y) & 8191)",
        b"(((x & 4095) + 1) * ((y & 4095) + 3) + ((z & 4095) + 5)) ^ (x * 17)",
        b"((x - (y - (z - x))) + (y * 9 - z * 5)) % 99991 + (x & z)",
        b"((x | 85) ^ (y | 170) ^ (z | 51)) + ((x + y) * 23) / ((y & 31) + 1)",
        b"((((x + 3) * 5 - y) ^ (z + 11)) + ((y + 7) * (z & 127))) % 524287",
    ];

    let mut comp = Compiler::new();
    let mut st = [0i64; 32];
    let mut total_insts: i64 = 0;
    let mut ck: i64 = 0;
    let mut rng: i64 = 112233445;

    for _rnd in 0..160 {
        for ei in 0..16 {
            comp.lex(exprs[ei]);
            comp.parse_or();
            comp.code.push(0);
            comp.imm.push(0);

            for _run in 0..100 {
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let x = rng & 65535;
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let y = rng & 65535;
                rng = (rng * 1103515245 + 12345) & 2147483647;
                let z = rng & 65535;

                let mut sp = 0usize;
                let mut ip = 0usize;
                let mut steps: i64 = 0;
                loop {
                    let op = comp.code[ip];
                    if op == 0 {
                        break;
                    }
                    steps += 1;
                    match op {
                        1 => {
                            st[sp] = comp.imm[ip];
                            sp += 1;
                        }
                        2 => {
                            st[sp] = x;
                            sp += 1;
                        }
                        3 => {
                            st[sp] = y;
                            sp += 1;
                        }
                        4 => {
                            st[sp] = z;
                            sp += 1;
                        }
                        5 => {
                            sp -= 1;
                            st[sp - 1] = (st[sp - 1] + st[sp]) & MASK30;
                        }
                        6 => {
                            sp -= 1;
                            st[sp - 1] = (st[sp - 1] - st[sp] + BASE30) & MASK30;
                        }
                        7 => {
                            sp -= 1;
                            st[sp - 1] = ((st[sp - 1] & 32767) * (st[sp] & 32767)) & MASK30;
                        }
                        8 => {
                            sp -= 1;
                            st[sp - 1] /= st[sp] + 1;
                        }
                        9 => {
                            sp -= 1;
                            st[sp - 1] %= st[sp] + 1;
                        }
                        10 => {
                            sp -= 1;
                            st[sp - 1] &= st[sp];
                        }
                        11 => {
                            sp -= 1;
                            st[sp - 1] |= st[sp];
                        }
                        12 => {
                            sp -= 1;
                            st[sp - 1] ^= st[sp];
                        }
                        13 => {
                            st[sp - 1] = (BASE30 - st[sp - 1]) & MASK30;
                        }
                        _ => {
                            st[sp - 1] ^= MASK30;
                        }
                    }
                    ip += 1;
                }
                total_insts += steps;
                ck = (ck * 31 + st[sp - 1]) % MOD_V;
            }
        }
    }

    println!("{}\n{}", total_insts, ck);
}
