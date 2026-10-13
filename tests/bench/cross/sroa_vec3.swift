struct Vec3 {
    var x: Float64
    var y: Float64
    var z: Float64
}

var v = Array(repeating: Vec3(x: 0, y: 0, z: 0), count: 256)
var i = 0
while i < 256 {
    v[i].x = Float64(i & 7)
    v[i].y = Float64((i * 3) & 7)
    v[i].z = Float64((i * 5) & 7)
    i += 1
}
var acc: Float64 = 0.0
var t: Int64 = 0
while t < 40000 {
    i = 0
    while i < 256 {
        acc += v[i].x * v[i].x + v[i].y * v[i].y + v[i].z * v[i].z
        i += 1
    }
    t += 1
}
print(Int64(acc))
