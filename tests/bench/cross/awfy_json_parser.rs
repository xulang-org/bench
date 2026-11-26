fn push_str(buf: &mut Vec<i64>, s: &str) {
    for b in s.bytes() {
        buf.push(b as i64);
    }
}

fn push_int(buf: &mut Vec<i64>, v: i64) {
    let mut x = v;
    if x < 0 {
        buf.push(45);
        x = -x;
    }
    if x == 0 {
        buf.push(48);
        return;
    }
    let mut digs = [0i64; 32];
    let mut dc = 0usize;
    while x > 0 {
        digs[dc] = 48 + (x % 10);
        dc += 1;
        x /= 10;
    }
    let mut i = dc;
    while i > 0 {
        i -= 1;
        buf.push(digs[i]);
    }
}

fn build_json_payload() -> Vec<i64> {
    let mut buf = Vec::with_capacity(8192);
    push_str(
        &mut buf,
        "{\"meta\":{\"id\":1000,\"active\":true,\"deleted\":false,\"note\":null,\"ratio\":-12.375e2},\"records\":[",
    );
    for r in 0i64..48 {
        if r > 0 {
            buf.push(44);
        }
        let v0 = (r * 37 + 11) % 997 - 400;
        let v1 = (r * 53 + 7) % 503;
        let v2 = -(r * 19 + 3);
        let v3 = r * 7 + 1;
        push_str(&mut buf, "{\"id\":");
        push_int(&mut buf, r);
        push_str(&mut buf, ",\"name\":\"item_");
        push_int(&mut buf, r);
        buf.push(92);
        buf.push(34);
        buf.push(118);
        buf.push(92);
        buf.push(92);
        buf.push(110);
        buf.push(34);
        if r % 2 == 0 {
            push_str(&mut buf, ",\"ok\":true,\"err\":null,\"vals\":[");
        } else {
            push_str(&mut buf, ",\"ok\":false,\"err\":null,\"vals\":[");
        }
        push_int(&mut buf, v0);
        buf.push(44);
        push_int(&mut buf, v1);
        buf.push(46);
        buf.push(48 + (r % 10));
        buf.push(44);
        push_int(&mut buf, v2);
        push_str(&mut buf, "e1,");
        push_int(&mut buf, v3);
        push_str(&mut buf, "],\"cfg\":{\"a\":");
        push_int(&mut buf, r * 3 + 1);
        push_str(&mut buf, ",\"b\":\"tag_");
        buf.push(48 + (r % 7));
        push_str(&mut buf, "\",\"c\":[true,false,null]}}");
    }
    push_str(&mut buf, "]}");
    buf
}

struct JsonParser<'a> {
    buf: &'a [i64],
    pos: usize,
    n: usize,
    kind: Vec<i64>,
    val: Vec<i64>,
    first_child: Vec<i64>,
    next_sib: Vec<i64>,
}

impl<'a> JsonParser<'a> {
    fn new(buf: &'a [i64]) -> Self {
        let n = buf.len();
        Self {
            buf,
            pos: 0,
            n,
            kind: Vec::with_capacity(1024),
            val: Vec::with_capacity(1024),
            first_child: Vec::with_capacity(1024),
            next_sib: Vec::with_capacity(1024),
        }
    }

    fn new_node(&mut self, k: i64, v: i64) -> i64 {
        let idx = self.kind.len() as i64;
        self.kind.push(k);
        self.val.push(v);
        self.first_child.push(-1);
        self.next_sib.push(-1);
        idx
    }

    fn skip_ws(&mut self) {
        while self.pos < self.n {
            let c = self.buf[self.pos];
            if c == 32 || c == 9 || c == 10 || c == 13 {
                self.pos += 1;
            } else {
                break;
            }
        }
    }

    fn parse_string_hash(&mut self) -> i64 {
        self.pos += 1;
        let mut h: i64 = 0;
        while self.pos < self.n {
            let c = self.buf[self.pos];
            self.pos += 1;
            if c == 34 {
                return h;
            }
            if c == 92 {
                if self.pos < self.n {
                    let ec = self.buf[self.pos];
                    self.pos += 1;
                    h = (h * 131 + ec + 256) % 1000000007;
                }
            } else {
                h = (h * 131 + c) % 1000000007;
            }
        }
        h
    }

    fn parse_number_hash(&mut self) -> i64 {
        let mut h: i64 = 0;
        if self.pos < self.n && self.buf[self.pos] == 45 {
            h = 45;
            self.pos += 1;
        }
        while self.pos < self.n && self.buf[self.pos] >= 48 && self.buf[self.pos] <= 57 {
            h = (h * 131 + self.buf[self.pos]) % 1000000007;
            self.pos += 1;
        }
        if self.pos < self.n && self.buf[self.pos] == 46 {
            h = (h * 131 + 46) % 1000000007;
            self.pos += 1;
            while self.pos < self.n && self.buf[self.pos] >= 48 && self.buf[self.pos] <= 57 {
                h = (h * 131 + self.buf[self.pos]) % 1000000007;
                self.pos += 1;
            }
        }
        if self.pos < self.n && (self.buf[self.pos] == 101 || self.buf[self.pos] == 69) {
            h = (h * 131 + 101) % 1000000007;
            self.pos += 1;
            if self.pos < self.n && (self.buf[self.pos] == 43 || self.buf[self.pos] == 45) {
                h = (h * 131 + self.buf[self.pos]) % 1000000007;
                self.pos += 1;
            }
            while self.pos < self.n && self.buf[self.pos] >= 48 && self.buf[self.pos] <= 57 {
                h = (h * 131 + self.buf[self.pos]) % 1000000007;
                self.pos += 1;
            }
        }
        h
    }

    fn parse_val(&mut self) -> i64 {
        self.skip_ws();
        let c = self.buf[self.pos];
        if c == 123 {
            self.pos += 1;
            let node = self.new_node(6, 0);
            let nu = node as usize;
            self.skip_ws();
            if self.pos < self.n && self.buf[self.pos] == 125 {
                self.pos += 1;
                return node;
            }
            let mut tail: i64 = -1;
            let mut cnt: i64 = 0;
            while self.pos < self.n {
                self.skip_ws();
                let kh = self.parse_string_hash();
                self.skip_ws();
                self.pos += 1;
                let child = self.parse_val();
                self.val[nu] = (self.val[nu] * 31 + kh) % 1000000007;
                if tail == -1 {
                    self.first_child[nu] = child;
                } else {
                    self.next_sib[tail as usize] = child;
                }
                tail = child;
                cnt += 1;
                self.skip_ws();
                if self.pos < self.n && self.buf[self.pos] == 44 {
                    self.pos += 1;
                } else {
                    self.pos += 1;
                    break;
                }
            }
            self.val[nu] = (self.val[nu] * 31 + cnt) % 1000000007;
            node
        } else if c == 91 {
            self.pos += 1;
            let node = self.new_node(5, 0);
            let nu = node as usize;
            self.skip_ws();
            if self.pos < self.n && self.buf[self.pos] == 93 {
                self.pos += 1;
                return node;
            }
            let mut tail: i64 = -1;
            let mut cnt: i64 = 0;
            while self.pos < self.n {
                let child = self.parse_val();
                if tail == -1 {
                    self.first_child[nu] = child;
                } else {
                    self.next_sib[tail as usize] = child;
                }
                tail = child;
                cnt += 1;
                self.skip_ws();
                if self.pos < self.n && self.buf[self.pos] == 44 {
                    self.pos += 1;
                } else {
                    self.pos += 1;
                    break;
                }
            }
            self.val[nu] = cnt;
            node
        } else if c == 34 {
            let h = self.parse_string_hash();
            self.new_node(4, h)
        } else if c == 116 {
            self.pos += 4;
            self.new_node(2, 1)
        } else if c == 102 {
            self.pos += 5;
            self.new_node(2, 0)
        } else if c == 110 {
            self.pos += 4;
            self.new_node(1, 0)
        } else {
            let h = self.parse_number_hash();
            self.new_node(3, h)
        }
    }

    fn walk(&self, u: i64) -> i64 {
        let uu = u as usize;
        let mut h = (self.kind[uu] * 1000003 + self.val[uu]) % 1000000007;
        let mut ch = self.first_child[uu];
        while ch != -1 {
            h = (h * 31 + self.walk(ch)) % 1000000007;
            ch = self.next_sib[ch as usize];
        }
        h
    }
}

fn main() {
    let mut buf = build_json_payload();
    let mut tot_nodes: i64 = 0;
    let mut tot_hash: i64 = 0;
    for r in 0i64..400 {
        let v = 1000 + r;
        buf[14] = 48 + (v / 1000) % 10;
        buf[15] = 48 + (v / 100) % 10;
        buf[16] = 48 + (v / 10) % 10;
        buf[17] = 48 + v % 10;
        let mut p = JsonParser::new(&buf);
        let root = p.parse_val();
        tot_nodes += p.kind.len() as i64;
        tot_hash = (tot_hash + p.walk(root)) % 1000000007;
    }
    println!("{}\n{}", tot_nodes, tot_hash);
}
