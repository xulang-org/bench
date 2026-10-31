# Osprey 24 题接入

来源：[Nimblesite/osprey](https://github.com/Nimblesite/osprey)，MIT；参考提交
`aeca2191136a2c1d64349b792118bc45e2557bfe` 的 `benchmarks/cases/`。
许可全文见 [LICENSE](LICENSE)。Xu 移植对照工作区已逐字节验证的 24 份
`scratch/*.xu`，并将相同算法直译到 Go / C / Rust / Swift。
[映射清单](cases.json) 给出原题、注册名和金标路径。

所有题保持 Osprey 原始规模；已有类似题继续保留，`osprey_` 名称避免冲突。
六个 seeded 题固定 `seed=1`，对应上游 stdin `0\n` 模式；全部端口均无需 stdin、
随机数或 `/dev/stdin`，便于在 Windows/macOS/Linux 使用同一金标。
没有为延长运行时间而增加重复次数；小规模原题可能短于 0.1 秒。

## 原题与本仓注册名

| Osprey | 注册名 | 原始工作量 | stdout（含尾随换行） |
|---|---|---|---:|
| `ackermann` | `ackermann` | Ackermann-Peter function ack(3,10) — deep non-tail recursion | `8189` |
| `binarytrees` | `osprey_binarytrees` | 1200 owning binary trees of depth 13; build then check (16383 nodes each) | `19659600` |
| `coins` | `coins` | Count ways to make 600 from coins [1,5,10,25,50] — combinatorial recursion (SICP) | `116727` |
| `collatz` | `collatz` | Sum of Collatz (3n+1) stopping times over 1..100000 — integer division n/2 in deep recursion | `10753840` |
| `coprime` | `osprey_coprime` | Count coprime pairs in a 2000x2000 grid — nested iteration + Euclidean gcd | `2433175` |
| `digitsum` | `digitsum` | Sum of decimal digit-sums over 1..2000000 — integer division n/10 and modulo | `55000002` |
| `exprtree` | `expr_tree` | 10 owning expression trees of depth 14; build then modular-evaluate | `900720437` |
| `factorial` | `factorial_mod` | Product 1..10,000,000 mod 1000000007 — multiplication-heavy fold | `682498929` |
| `fib` | `osprey_fib` | Naive recursive Fibonacci, fib(35) — function-call & recursion overhead | `9227465` |
| `gcdsum` | `gcd_sum` | Sum of gcd(i,1234567) for i in 1..1999999 — Euclidean recursion, modulo heavy | `7201567` |
| `hanoi` | `hanoi` | Towers of Hanoi move count (n=25) — exponential double recursion | `33554431` |
| `isqrt` | `isqrt` | Sum of integer square roots over 1..1000000 — Newton's method, integer division heavy | `666167500` |
| `josephus` | `josephus` | Josephus survivor index (n=10,000,000, k=7) — modular iteration | `1400177` |
| `listops` | `osprey_listops` | 8 growable vectors x 4000 integers; recursive sum and count-below traversals | `15992435` |
| `mergesort` | `merge_sort` | 8 x 2000 values; alternating split, recursive merge sort with fresh vectors; rank checksum | `563434287` |
| `mutual` | `mutual_recursion` | Mutually recursive parity of i%1000, 1 <= i < 130000 | `64999` |
| `nestedloop` | `osprey_nestedloop` | Triple-nested loop 250^3 accumulating (i*j*k) mod 1000000007 — nested iteration | `255643180` |
| `pascal` | `pascal` | Binomial C(27,13) via naive un-memoised Pascal recursion — exponential recursion | `20058300` |
| `powmod` | `powmod` | Sum i^20 mod 1000000007, 1 <= i < 1000000; twenty modular multiplies | `980475159` |
| `primes` | `osprey_primes` | Count primes below 200000 by trial division — integer modulo in a hot loop | `17984` |
| `quicksort` | `osprey_quicksort` | 8 x 2000 values; first-element pivot, two partition passes, fresh vectors; rank checksum | `563434287` |
| `tak` | `tak` | Takeuchi function tak(32,16,8) — heavy ternary self-recursion | `9` |
| `textstats` | `osprey_textstats` | 200000 tokens, 8 words; length + contains(o) + startsWith(t) | `1574956` |
| `wordfreq` | `word_frequency` | 200000 tokens, 8 words; string-keyed frequency map, weighted counts | `900036` |

## 一致性与数据表示

`int` 与算术值均为 i64，计数循环使用 while（Go 的条件式 for）。保持未记忆化递归、
试除素数、首元素 pivot 的两遍分区、交替分半的归并排序；不用筛法、标准库排序、
模幂平方优化或 DP 替换基准算法。独立 Python oracle 可以用这些不同算法核验结果。

`listops` 按已验证 Xu 版本使用 growable vector，构造后分别递归求和、计数；所有端口
都执行两次遍历。两种排序每次分割/合并都生成新 vector，C 显式扩容、释放；
不以原地排序代替分配型排序。容器的增长策略和分配器仍由各语言实现决定。

`binarytrees` 为 1200 棵、深度 13 的 owning 树，每棵检查 16383 个 Node，Leaf 为 0。
`exprtree` 构建 10 棵深度 14 的 owning 算术树后再递归求值，不改成边构建边求值。
Xu 采用验证过的 owning 接口树；Rust 用 Box/enum，C 用指针和标签，Go/Swift 用引用节点。
C 在每棵树完成后显式释放，对应其他 owning 端口的生命周期；Go 的回收由 GC 决定。
因此结果包含语言本身的分派、分配、释放成本，不能解释成完全相同的内存布局。

`wordfreq` 的每个 token 均先查字符串键再更新 map。C 实现 FNV-1a + 线性探测的
字符串哈希表，16 槽容纳 8 种固定词；不使用词编号直接索引计数数组。
其余端口使用语言 map/HashMap/Dictionary，哈希函数和 key 所有权由语言容器决定。
词频结果按固定词序加权，避免依赖哈希表遍历顺序。

## 注册和验证约定

Xu 文件位于 `tests/bench/<注册名>.xu`，四种独立端口位于
`tests/bench/cross/<注册名>.{go,c,rs,swift}`；每题以 CORE 四语言注册到
`scripts/bench_crosslang.py`，描述带 `Osprey:`，stdout 常量与本目录
[golden](golden/) 的上游 expected.txt 字节相同。`tests/test_microgap.py` 核验
24 题完整性、所有端口存在、注册金标与文件一致，并用独立数学公式/算法核验结果。
新题不加入 Game 注册表，也不更改其官方金标。

本机验收需 `make test`、`make list` 和新题真实横测。Swift 缺失时仍保留端口并明确
标记未验证；不能把未安装的编译器当作成功样本。C 默认优先 Clang，主机无 Clang 时
回退 GCC；也可用 `--cc=gcc` 显式选择，报告标签保留实际编译器。Apple 交叉目标要求 Clang。

## 跑法

从仓库根执行，`XU_ROOT` 须提供与产品编译器配套的标准库和 hosted wrapper。

```sh
export XU_ROOT=/path/to/matching/xu
make list
make test
BENCHES=$(python3 -c 'import json; print(",".join(c["bench"] for c in json.load(open("tests/bench/osprey/cases.json"))["cases"]))')
python3 scripts/bench_crosslang.py --xu=/path/to/xu --benches="$BENCHES" \
  --quick --iters=3 --discard-first --sample-ms=0 --out=reports/osprey.txt
```

`--quick` 省去调试档和编译时间，仍运行 C/Rust O1、O2、O3。横测每次核对固定 stdout，
wall/CPU 不包含编译；Linux RSS 按本仓独立重跑协议核验。性能结论需同时记录源码提交、
产品编译器身份、标准库来源、平台、输入规模、预跑与采样方式。
