func main() {
    let n = 2000000
    var isPrime = [Int]()
    isPrime.reserveCapacity(n + 1)
    var i = 0
    while i <= n {
        isPrime.append(1)
        i += 1
    }
    isPrime[0] = 0
    isPrime[1] = 0
    var p = 2
    while p * p <= n {
        if isPrime[p] == 1 {
            var j = p * p
            while j <= n {
                isPrime[j] = 0
                j += p
            }
        }
        p += 1
    }
    var count: Int64 = 0
    var total: Int64 = 0
    var k = 2
    while k <= n {
        if isPrime[k] == 1 {
            count += 1
            total += Int64(k)
        }
        k += 1
    }
    print(count)
    print(total)
}
main()
