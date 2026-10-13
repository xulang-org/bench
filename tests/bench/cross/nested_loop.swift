var s: Int64 = 0
var i: Int64 = 0
while i < 8000 {
    var j: Int64 = 0
    while j < 8000 {
        s += (i * j) & 1023
        j += 1
    }
    i += 1
}
print(s)
