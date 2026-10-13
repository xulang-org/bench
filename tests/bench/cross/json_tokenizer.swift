func tokenize(_ src: [UInt8]) -> (Int, Int64) {
    let n = src.count
    var pos = 0
    var count = 0
    var chk: Int64 = 0
    while pos < n {
        let c = src[pos]
        if c == 32 || c == 9 || c == 10 || c == 13 {
            pos += 1
            continue
        }
        var tType: Int64 = 0
        var tLen: Int64 = 0
        if c == 123 {
            tType = 1; tLen = 1; pos += 1
        } else if c == 125 {
            tType = 2; tLen = 1; pos += 1
        } else if c == 91 {
            tType = 3; tLen = 1; pos += 1
        } else if c == 93 {
            tType = 4; tLen = 1; pos += 1
        } else if c == 58 {
            tType = 5; tLen = 1; pos += 1
        } else if c == 44 {
            tType = 6; tLen = 1; pos += 1
        } else if c == 34 {
            tType = 7
            let start = pos
            pos += 1
            while pos < n {
                let ch = src[pos]
                if ch == 92 {
                    pos += 2
                } else if ch == 34 {
                    pos += 1
                    break
                } else {
                    pos += 1
                }
            }
            tLen = Int64(pos - start)
        } else if c == 45 || (c >= 48 && c <= 57) {
            tType = 8
            let start = pos
            if c == 45 { pos += 1 }
            while pos < n && (src[pos] >= 48 && src[pos] <= 57) {
                pos += 1
            }
            if pos < n && src[pos] == 46 {
                pos += 1
                while pos < n && (src[pos] >= 48 && src[pos] <= 57) {
                    pos += 1
                }
            }
            tLen = Int64(pos - start)
        } else if c == 116 {
            tType = 9; tLen = 4; pos += 4
        } else if c == 102 {
            tType = 10; tLen = 5; pos += 5
        } else if c == 110 {
            tType = 11; tLen = 4; pos += 4
        } else {
            pos += 1
            continue
        }
        count += 1
        chk = (chk &* 37 &+ tType &* 101 &+ tLen) % 1000000007
    }
    return (count, chk)
}

func main() {
    let base = "{\"project\":\"Xu\",\"version\":1.0,\"active\":true,\"count\":100,\"flag\":false,\"note\":null,\"data\":[1,2,-3,40]}"
    let full = String(repeating: base, count: 10)
    let bytes = Array(full.utf8)
    var total: Int64 = 0
    for _ in 0..<1000 {
        let (_, c) = tokenize(bytes)
        total = (total &* 31 &+ c) % 1000000007
    }
    print(total)
}

main()
