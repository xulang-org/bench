"""Independent goldens for the added kernels, plus their registry contract."""
from functools import lru_cache
from math import comb, gcd, isqrt
from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bench_crosslang as suite

MOD = 1000000007
OSPREY = suite.BENCH_ROOT / "tests" / "bench" / "osprey"
CASES = json.loads((OSPREY / "cases.json").read_text())["cases"]
NAMES = tuple(c["bench"] for c in CASES)


def check(name, value):
    assert suite.BY_NAME[name].expect == f"{value}\n"


@pytest.mark.parametrize("name", NAMES)
def test_complete_standalone_ports(name):
    assert suite.BY_NAME[name].langs == suite.CORE
    case = next(c for c in CASES if c["bench"] == name)
    assert suite.BY_NAME[name].face.startswith("Osprey:")
    assert suite.BY_NAME[name].expect.encode() == (OSPREY / case["golden"]).read_bytes()
    assert suite.xu_src(name).read_text().splitlines()[0] == "@main"
    for ext in suite.CORE:
        assert suite.cross_src(name, ext).is_file()


def test_closed_form_goldens():
    check("ackermann", (1 << (10 + 3)) - 3)
    check("hanoi", (1 << 25) - 1)
    check("pascal", comb(27, 13))
    check("digitsum", 2 * 6 * 45 * 10**5 + 10**6 + 2)
    check("mutual_recursion", (130000 - 1) // 2)


def test_coins_via_dynamic_programming():
    ways = [1] + [0] * 600
    for coin in (1, 5, 10, 25, 50):
        for amount in range(coin, 601):
            ways[amount] += ways[amount - coin]
    check("coins", ways[600])


def test_collatz_via_iterative_memoisation():
    # No recursion, and retain only starts in the measured range.
    cache = {1: 0}
    total = 0
    for start in range(1, 100001):
        n = start
        path = []
        while n not in cache:
            path.append(n)
            n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps = cache[n]
        for n in reversed(path):
            steps += 1
            if n <= 100000:
                cache[n] = steps
        total += steps
    check("collatz", total)


def test_factorial_mod_via_python_integers():
    value = 1
    for i in range(1, 10000001):
        value = value * i % MOD
    check("factorial_mod", value)


def test_gcd_and_isqrt_via_standard_library():
    check("gcd_sum", sum(gcd(i, 1234567) for i in range(1, 2000000)))
    check("isqrt", sum(isqrt(i) for i in range(1, 1000001)))


def test_josephus_via_k_step_reduction():
    # O(k log n) reduction instead of the benchmark's O(n) recurrence.
    def survivor(n, k):
        if n == 1:
            return 0
        if k > n:
            return (survivor(n - 1, k) + k) % n
        result = survivor(n - n // k, k) - n % k
        return result + n if result < 0 else result + result // (k - 1)
    check("josephus", survivor(10000000, 7))


def test_powmod_via_modular_squaring():
    check("powmod", sum(pow(i, 20, MOD) for i in range(1, 1000000)) % MOD)


def test_takeuchi_via_memoisation():
    @lru_cache(None)
    def tak(x, y, z):
        return tak(tak(x-1, y, z), tak(y-1, z, x), tak(z-1, x, y)) if x > y else z
    check("tak", tak(32, 16, 8))


def token_hash(seed, index):
    # Two MINSTD steps are one multiplication by 16807**2 modulo its modulus.
    return (seed + index) * pow(16807, 2, 2147483647) % 2147483647


def test_expression_tree_via_direct_evaluation():
    # Evaluate mathematically without allocating or indexing a node arena.
    def value(seed, index, depth):
        h = token_hash(seed, index)
        if depth == 0:
            return h % 1000
        left = value(seed, 2 * index + 1, depth - 1)
        right = value(seed, 2 * index + 2, depth - 1)
        return (left + right if h % 2 == 0 else left * right) % MOD
    check("expr_tree", sum(value(1 + 7*t, 1, 14) for t in range(10)) % MOD)


def test_merge_sort_via_builtin_sort():
    total = 0
    for t in range(8):
        ordered = sorted(token_hash(1 + 131*t, i) % 100000 for i in range(2000))
        total += sum(rank * value for rank, value in enumerate(ordered, 1))
    check("merge_sort", total % MOD)
    check("osprey_quicksort", total % MOD)


def test_word_frequency_via_token_weights():
    # Sum token weights directly, without a map or dependence on its iteration order.
    check("word_frequency", sum(1 + token_hash(1, i) % 8 for i in range(200000)))


def test_all_original_cases_are_present():
    expected = set("ackermann binarytrees coins collatz coprime digitsum exprtree "
                   "factorial fib gcdsum hanoi isqrt josephus listops mergesort mutual "
                   "nestedloop pascal powmod primes quicksort tak textstats wordfreq".split())
    assert len(CASES) == len(NAMES) == len(set(NAMES)) == 24
    assert {c["case"] for c in CASES} == expected


def test_binary_tree_and_nestedloop_via_formulas():
    check("osprey_binarytrees", 1200 * ((1 << 14) - 1))
    check("osprey_nestedloop", pow(250 * 251 // 2, 3, MOD))


def test_fib_via_iteration():
    a, b = 0, 1
    for _ in range(35):
        a, b = b, a + b
    check("osprey_fib", a)


def test_primes_via_sieve():
    prime = bytearray(b"\x01") * 200000
    prime[:2] = b"\x00\x00"
    for d in range(2, isqrt(199999) + 1):
        if prime[d]:
            prime[d*d::d] = b"\x00" * len(prime[d*d::d])
    check("osprey_primes", sum(prime))


def test_coprime_via_totient_sieve():
    phi = list(range(2001))
    for p in range(2, 2001):
        if phi[p] == p:
            for multiple in range(p, 2001, p):
                phi[multiple] -= phi[multiple] // p
    check("osprey_coprime", 2 * sum(phi[1:]) - 1)


def test_listops_via_direct_iteration():
    total = 0
    for t in range(8):
        values = [token_hash(1 + 131*t, i) % 1000 for i in range(4000)]
        total += sum(values) + sum(v < 500 for v in values)
    check("osprey_listops", total % MOD)


def test_textstats_via_precomputed_word_scores():
    words = ("the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog")
    scores = [len(w) + 7 * ("o" in w) + 3 * w.startswith("t") for w in words]
    check("osprey_textstats", sum(scores[token_hash(1, i) % 8] for i in range(200000)))


@pytest.mark.parametrize("name", ("clang", "gcc"))
def test_c_profiles_preserve_levels_and_compiler_identity(name):
    assert suite.c_profiles(name) == tuple(
        (n, f"{name} -O{n}", [f"-O{n}"], f"o{n}") for n in (1, 2, 3)
    )


def test_c_selection_falls_back_only_on_host(monkeypatch):
    monkeypatch.setattr(suite, "which", lambda name: "/bin/gcc" if name == "gcc" else None)
    assert suite.select_c_compiler(None, None) == "gcc"
    assert suite.select_c_compiler(None, "macos-x64") == "clang"
    with pytest.raises(SystemExit, match="requires --cc=clang"):
        suite.select_c_compiler("gcc", "macos-x64")
    with pytest.raises(SystemExit, match="unavailable"):
        suite.select_c_compiler("clang", None)
    monkeypatch.setattr(suite, "which", lambda name: f"/bin/{name}")
    assert suite.select_c_compiler(None, None) == "clang"
    assert suite.select_c_compiler("gcc", None) == "gcc"
