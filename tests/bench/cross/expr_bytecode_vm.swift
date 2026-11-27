let modV = 1000000007
let mask30 = 1073741823
let base30 = 1073741824

final class Compiler {
    var tk: [Int] = []
    var tv: [Int] = []
    var pos = 0
    var code: [Int] = []
    var imm: [Int] = []

    func lex(_ s: [Int]) {
        tk.removeAll(keepingCapacity: true)
        tv.removeAll(keepingCapacity: true)
        var i = 0
        let n = s.count
        while i < n {
            let b = s[i]
            if b == 32 {
                i += 1
            } else if b >= 48 && b <= 57 {
                var v = 0
                while i < n && s[i] >= 48 && s[i] <= 57 {
                    v = (v * 10 + (s[i] - 48)) & mask30
                    i += 1
                }
                tk.append(1)
                tv.append(v)
            } else {
                let kind: Int
                switch b {
                case 120: kind = 2
                case 121: kind = 3
                case 122: kind = 4
                case 43: kind = 5
                case 45: kind = 6
                case 42: kind = 7
                case 47: kind = 8
                case 37: kind = 9
                case 38: kind = 10
                case 124: kind = 11
                case 94: kind = 12
                case 126: kind = 13
                case 40: kind = 14
                default: kind = 15
                }
                tk.append(kind)
                tv.append(0)
                i += 1
            }
        }
        tk.append(0)
        tv.append(0)
        pos = 0
        code.removeAll(keepingCapacity: true)
        imm.removeAll(keepingCapacity: true)
    }

    func parsePrim() {
        let t = tk[pos]
        if t == 1 {
            code.append(1)
            imm.append(tv[pos])
            pos += 1
        } else if t == 2 || t == 3 || t == 4 {
            code.append(t)
            imm.append(0)
            pos += 1
        } else {
            pos += 1
            parseOr()
            pos += 1
        }
    }

    func parseUnary() {
        let t = tk[pos]
        if t == 6 {
            pos += 1
            parseUnary()
            code.append(13)
            imm.append(0)
        } else if t == 13 {
            pos += 1
            parseUnary()
            code.append(14)
            imm.append(0)
        } else {
            parsePrim()
        }
    }

    func parseMul() {
        parseUnary()
        while tk[pos] == 7 || tk[pos] == 8 || tk[pos] == 9 {
            let op = tk[pos]
            pos += 1
            parseUnary()
            code.append(op)
            imm.append(0)
        }
    }

    func parseAdd() {
        parseMul()
        while tk[pos] == 5 || tk[pos] == 6 {
            let op = tk[pos]
            pos += 1
            parseMul()
            code.append(op)
            imm.append(0)
        }
    }

    func parseAnd() {
        parseAdd()
        while tk[pos] == 10 {
            pos += 1
            parseAdd()
            code.append(10)
            imm.append(0)
        }
    }

    func parseXor() {
        parseAnd()
        while tk[pos] == 12 {
            pos += 1
            parseAnd()
            code.append(12)
            imm.append(0)
        }
    }

    func parseOr() {
        parseXor()
        while tk[pos] == 11 {
            pos += 1
            parseXor()
            code.append(11)
            imm.append(0)
        }
    }
}

func run() {
    let rawExprs = [
        "((x + y) * (z + 7) - (x ^ y)) / ((z & 15) + 1) + (x % 97)",
        "(~x & 65535) + ((y * 13 + z) ^ (x + y + z)) - (y / 3)",
        "((x * 3 + y * 5 + z * 7) ^ (x * 11 - y)) + ((z | 255) & (x + 1023))",
        "-(x - y) + (z * (x & 255) + (y % 31)) ^ (~z & 4095)",
        "(((x + 17) * (y + 29)) % 65521) + ((z ^ (x + y)) / ((x & 7) + 1))",
        "((x | y) & (y | z) & (z | x)) + ((x ^ y ^ z) * 19) - (z % 17)",
        "(x + (y + (z + (x * 3 + (y * 5 - z))))) & 1048575",
        "((x / 5 + y / 7 + z / 11) * (x % 13 + y % 17 + 1)) ^ (x + z)",
        "((~x & 1023) * (~y & 1023) + (~z & 1023)) % 1000003",
        "(((x ^ 12345) + (y ^ 6789)) * 7) / ((z % 23) + 2) + (y & 511)",
        "(x * (y & 63) - y * (z & 63) + z * (x & 63)) ^ ((x + y) | z)",
        "((x + y + z) * (x + y + z)) / (x % 29 + y % 31 + 3) + (~(x & y) & 8191)",
        "(((x & 4095) + 1) * ((y & 4095) + 3) + ((z & 4095) + 5)) ^ (x * 17)",
        "((x - (y - (z - x))) + (y * 9 - z * 5)) % 99991 + (x & z)",
        "((x | 85) ^ (y | 170) ^ (z | 51)) + ((x + y) * 23) / ((y & 31) + 1)",
        "((((x + 3) * 5 - y) ^ (z + 11)) + ((y + 7) * (z & 127))) % 524287"
    ]
    let exprs = rawExprs.map { Array($0.utf8).map { Int($0) } }

    let comp = Compiler()
    var st = [Int](repeating: 0, count: 32)
    var totalInsts = 0
    var ck = 0
    var rng = 112233445

    for _ in 0..<160 {
        for ei in 0..<16 {
            comp.lex(exprs[ei])
            comp.parseOr()
            comp.code.append(0)
            comp.imm.append(0)

            for _ in 0..<100 {
                rng = (rng * 1103515245 + 12345) & 2147483647
                let x = rng & 65535
                rng = (rng * 1103515245 + 12345) & 2147483647
                let y = rng & 65535
                rng = (rng * 1103515245 + 12345) & 2147483647
                let z = rng & 65535

                var sp = 0
                var ip = 0
                var steps = 0
                while true {
                    let op = comp.code[ip]
                    if op == 0 {
                        break
                    }
                    steps += 1
                    switch op {
                    case 1:
                        st[sp] = comp.imm[ip]
                        sp += 1
                    case 2:
                        st[sp] = x
                        sp += 1
                    case 3:
                        st[sp] = y
                        sp += 1
                    case 4:
                        st[sp] = z
                        sp += 1
                    case 5:
                        sp -= 1
                        st[sp - 1] = (st[sp - 1] + st[sp]) & mask30
                    case 6:
                        sp -= 1
                        st[sp - 1] = (st[sp - 1] - st[sp] + base30) & mask30
                    case 7:
                        sp -= 1
                        st[sp - 1] = ((st[sp - 1] & 32767) * (st[sp] & 32767)) & mask30
                    case 8:
                        sp -= 1
                        st[sp - 1] = st[sp - 1] / (st[sp] + 1)
                    case 9:
                        sp -= 1
                        st[sp - 1] = st[sp - 1] % (st[sp] + 1)
                    case 10:
                        sp -= 1
                        st[sp - 1] = st[sp - 1] & st[sp]
                    case 11:
                        sp -= 1
                        st[sp - 1] = st[sp - 1] | st[sp]
                    case 12:
                        sp -= 1
                        st[sp - 1] = st[sp - 1] ^ st[sp]
                    case 13:
                        st[sp - 1] = (base30 - st[sp - 1]) & mask30
                    default:
                        st[sp - 1] = st[sp - 1] ^ mask30
                    }
                    ip += 1
                }
                totalInsts += steps
                ck = (ck * 31 + st[sp - 1]) % modV
            }
        }
    }

    print("\(totalInsts)\n\(ck)")
}

run()
