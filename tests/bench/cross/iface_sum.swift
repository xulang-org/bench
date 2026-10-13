protocol Src {
    func val() -> Int64
}

struct A: Src {
    var x: Int64
    func val() -> Int64 { x }
}

struct B: Src {
    var x: Int64
    func val() -> Int64 { x * 2 }
}

let xs: [Src] = [A(x: 1), B(x: 2)]
var s: Int64 = 0
var i: Int64 = 0
while i < 8_000_000 {
    s += xs[Int(i & 1)].val()
    i += 1
}
print(s)
