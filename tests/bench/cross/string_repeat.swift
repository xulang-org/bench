let seed = "alpha,beta,gamma,delta;omega,phi,chi;lambda,mu,nu"
var total: Int64 = 0
for i in 0..<25000 {
    let out = String(repeating: seed, count: 384 + (i & 1))
    total += Int64(out.utf8.count)
    total += Int64(out.utf8[out.utf8.index(out.utf8.startIndex, offsetBy: 100)])
}
print(total)
