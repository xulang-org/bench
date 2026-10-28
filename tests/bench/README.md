# 语言能力效率套件

按常规语言能力面（循环、递归、字符串、数组、矩阵下标、排序、浮点、方法、并发、哈希、map、接口派发、match/switch、函数值），而不是 SPECcpu。

以下列出部分负载；当前负载与对照语言清单以仓库根目录的 `make list` 为准。
本页的 `make` 和 `scripts/` 命令也从仓库根目录执行，环境准备见[根 README](../../README.md)。

| 负载 | 度量面 | Xu | 对照 |
|---|---|---|---|
| `startup` | 进程启动 + 空 `main` | `startup.xu` | Go / C / Rust / Swift |
| `loop_sum` | 整数循环 | `loop_sum.xu` | Go / C / Rust / Swift |
| `fib` | 递归调用 | `fib.xu` | 同上 |
| `nested_loop` | 嵌套循环 | `nested_loop.xu` | 同上 |
| `method_sum` | 结构体方法 | `method_sum.xu` | 同上 |
| `f64_sum` | f64 算术 | `f64_sum.xu` | 同上 |
| `matmul` | 嵌套循环 + 数组下标（i64 朴素乘） | `matmul.xu` | 同上 |
| `string_build` | 字符串增长 + 字节扫描 | `string_build.xu` | 同上 |
| `builder` | `strings.Builder.write_byte` + ByteView 扫描 | `builder.xu` | Go / C / Rust / Swift |
| `byte_view` | ByteView `index_byte` / `index` 100k haystack | `byte_view.xu` | Go / C / Rust / Swift |
| `array_ops` | 数组增长 + 索引 | `array_ops.xu` | 同上 |
| `file_roundtrip` | 32 × 512KiB 文件写入 + 读取 + 校验 | `write_file` / `read_file` | 各语言文件 API；每次在独立临时目录运行 |
| `sort_lcg` | LCG + stdlib 排序 | `sort.ints` | 各语言 stdlib sort |
| `algorithm_search` | 标准包二分查找热路径 | `sort.search_ints` | C `lower_bound` 同算法 |
| `sha256_chain` | 链式 SHA-256 | `crypto/sha256` | Go `crypto/sha256`；C/Rust 同算法直译；Swift CryptoKit |
| `chan_ping` | 缓冲 channel | `chan` + `xu` worker | Go goroutine+chan；Rust `sync_channel`+线程（模型不同，仅作参照） |
| `math_bits` | 位计数/旋转/翻转热路径 | `math/bits` | arm64/x64 直接调用对齐 Clang 指令选择 |
| `map_ops` | 20 万次 map 插入 + 查找 | 语言 `map` | Go map / C 开地址表 / Rust HashMap / Swift Dictionary |
| `iface_sum` | 800 万次接口方法 | `struct@` 动态派发 | Go interface / C 函数指针表 / Rust `dyn Trait` / Swift protocol |
| `match_sum` | 2400 万次 8 路 match | 分支表 | Go/C/Swift `switch`；Rust `match` |
| `fn_val_sum` | 800 万次函数值调用 | 间接调用 | Go func 值 / C 函数指针 / Rust `fn` / Swift 函数值 |
| `copy_bytes` | 1Mi 元素 × 80 遍下标拷贝 | 描述符 + LoadIndex/StoreIndex 带宽 | 同算法 while 拷贝，不用 memcpy |
| `sroa_vec3` | 256 个 `{x,y,z f64}` × 40000 归约 | AoS 字段 / SROA / FieldRMW | C 结构体数组 |
| `scan_dep` | 4096 宽 prefix-add × 20000 | 进位依赖、skip-store | 同算法标量链 |
| `chase_index` | 65536 环 × 20e6 步 | 数据相关下标 / gather | 同算法间接索引 |

规则：同算法直译，`int` = i64，计数用 `while`，stdout checksum 必须逐字节一致。不是各语言最快写法（Go 不用 `for range` 特化、C 不做手写 SIMD）。跨语言测量方法见[根 README](../../README.md#测量口径)：整程序 wall、best+median、峰值 RSS + CPU(user+sys)、可选 `--discard-first`。结果仅覆盖这些负载与所测环境。

- Xu 运行时对拍：`scripts/bench_runtime.sh` / `make runtime`（同一 hosted 产品编译器分别以 O0 与默认优化编译，核对输出；耗时取 best-of，默认 5 次，可用 `--iters=N` 调整）。
- 优化档：`scripts/bench_opt_full.sh` / `make opt-full`（运行 wall+RSS+CPU+体积+曲线 + 编译 wall/RSS + Xu `--timings` 分相；写 `reports/bench_opt_levels.latest.txt`）。只看上次结果：`./scripts/bench_opt_full.sh --digest`。门禁 `make opt-levels ARGS="--check"` / `scripts/bench_opt_levels.sh --check`：选定负载的 Xu O0–O3 + `--no-regcache` + `-O1 --ra=2` + `-O2 --ra=1`，stdout 必须一致；超时阈值为默认档耗时的 5×（至少 1 秒）；短负载墙钟相对 CPU 多出 >40ms 失败；O2/O3 不得慢于 O1（5% 且 0.5ms）。`--quick` 是 5 负载子集。
- 优化阶段二分：`python3 scripts/opt_stage_bisect.py --bench=iface_sum --opt=2`（hosted 产品编译器的 `--dump-opt-stages` / `--opt-stop`）。
- 跨语言：`make crosslang`（通过 hosted seed resolver 选择产品编译器，再由 hermetic wrapper 编译 Xu 负载；此入口不执行自举固定点检查）
  - 直接运行脚本时也使用同一 resolver；默认从 Xu 仓库的 `bin/xu` 或 hosted snapshot 选择，`--xu=PATH` 可指定另一个 hosted 产品编译器
  - `--quick` 省去对照语言的调试档和编译时间；Xu 使用默认优化，Clang、rustc 的 O1/O2/O3 仍全部参与（安静机器；热机会偏慢）
  - `--benches=loop_sum,fib` 子集
  - `--benches=math_bits,algorithm_search --xu-target=macos-x64` 由产品 `xu` 交叉生成 X64，并与 `clang -arch x86_64` 在 Rosetta 下对照
  - `--discard-first` 丢掉冷缓存首跑
  - `--iters=N` 改采样次数（默认 7）
  - `--sample-ms=5` 运行中 RSS 采样间隔（`0` 关曲线）；SVG/CSV → `<out>.curves/`
  - `--list` 列出负载
- Xu 仓库的组合评测：`make -C ../xu bench-language`。它汇总选定的跨语言性能矩阵、优化器门禁、产品 fixtures（含标准库/I/O/并发）、安全、跨平台及 hosted 自举固定点检查；覆盖范围由所选套件与运行平台决定，报告默认写到 Xu 仓库的 `docs/audit/language_eval.latest.md`。直接调用脚本时从 Xu 仓库根执行，例如 `cd ../xu` 后运行 `python3 scripts/language_eval.py --quick`；按面运行：`--suites=performance,optimizer`；只查看命令：`--dry-run`。
- X64 产品正确性：`make -C ../xu verify-product-math-x64`（`math_bits` / `math_bits_extra` / `f64_basic` / `std_math`，均由 `bin/xu` 生成并在 Rosetta/原生 X64 执行）
- X64 算法正确性：`make -C ../xu verify-product-algorithm-x64`（`sort` / `slices` / `container/heap`，均由 `bin/xu` 生成并执行）

## Benchmarks Game 套件

对齐 [Benchmarks Game](https://benchmarksgame-team.pages.debian.net/benchmarksgame/)：[`game/`](game/)（Xu + C/C++/Rust/Go）。

```bash
make game
# 或
python3 scripts/bench_game.py --verify-only
python3 scripts/bench_game.py --out reports/bench_game.latest.txt --report reports/game.md
```

报告：[`reports/game.md`](../../reports/game.md)（运行 `make game` 后生成）。
