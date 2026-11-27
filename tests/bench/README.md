# 语言能力效率套件

按常规语言能力面（循环、递归、字符串、数组、矩阵下标、排序、浮点、方法、并发、哈希、map、接口派发、match/switch、函数值），而不是 SPECcpu。

新增 [Osprey 24 题](osprey/README.md) 保持上游原始算法、规模和确定性金标，
与既有相似题分别注册；每题提供 Xu / Go / C / Rust / Swift 端口。

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
| `http_concurrent` | HTTP 高并发端到端吞吐（16 并发 × 200 请求，自环回） | `net/http` server + 裸 TCP client | Go `net/http`+goroutine；Rust `std::net`+OS 线程（无 crate，server 手写最小子集） |
| `math_bits` | 位计数/旋转/翻转热路径 | `math/bits` | arm64/x64 直接调用对齐 Clang 指令选择 |
| `map_ops` | 20 万次 map 插入 + 查找 | 语言 `map` | Go map / C 开地址表 / Rust HashMap / Swift Dictionary |
| `iface_sum` | 800 万次接口方法 | `struct@` 动态派发 | Go interface / C 函数指针表 / Rust `dyn Trait` / Swift protocol |
| `match_sum` | 2400 万次 8 路 match | 分支表 | Go/C/Swift `switch`；Rust `match` |
| `fn_val_sum` | 800 万次函数值调用 | 间接调用 | Go func 值 / C 函数指针 / Rust `fn` / Swift 函数值 |
| `copy_bytes` | 1Mi 元素 × 80 遍下标拷贝 | 描述符 + LoadIndex/StoreIndex 带宽 | 同算法 while 拷贝，不用 memcpy |
| `sroa_vec3` | 256 个 `{x,y,z f64}` × 40000 归约 | AoS 字段 / SROA / FieldRMW | C 结构体数组 |
| `scan_dep` | 4096 宽 prefix-add × 20000 | 进位依赖、skip-store | 同算法标量链 |
| `chase_index` | 65536 环 × 20e6 步 | 数据相关下标 / gather | 同算法间接索引 |
| `avl_tree` | AVL 平衡二叉树（8 万次插入 + 30 万次查找） | `avl_tree.xu` | Go / C / Rust / Swift |
| `chacha20_stream` | ChaCha20 流密码 3 万块生成 | `chacha20_stream.xu` | Go / C / Rust / Swift |
| `huffman_coding` | Huffman 建树 + 2 万符号位流编码与 50 轮解码 | `huffman_coding.xu` | Go / C / Rust / Swift |
| `json_tokenizer` | JSON 词法扫描器（1000 轮） | `json_tokenizer.xu` | Go / C / Rust / Swift |
| `lzw_codec` | LZW 压缩与解压（LSB 8-bit，2500 轮） | `lzw_codec.xu` | Go / C / Rust / Swift |
| `plb2_nqueen` | [PLB2](plb2/README.md) 15 皇后位运算迭代回溯 | `plb2_nqueen.xu` | Go / C / Rust / Swift |
| `plb2_sudoku` | [PLB2](plb2/README.md) `kudoku` 精确覆盖数独求解（10 题 × 20 轮） | `plb2_sudoku.xu` | Go / C / Rust / Swift |
| `plb2_bedcov` | [PLB2](plb2/README.md) 隐式区间树重叠统计（20 万 × 20 万） | `plb2_bedcov.xu` | Go / C / Rust / Swift |
| `thread_ring` | 503 节点并发令牌环（10 万次传递） | `thread_ring.xu` | Go / Rust |
| `skynet` | 10 叉树协程扇出汇总（2 轮 × 1111 任务） | `skynet.xu` | Go |
| `scimark_montecarlo` | [SciMark2](scimark2/README.md) 蒙特卡洛圆周率采样（500 万次） | `scimark_montecarlo.xu` | Go / C / Rust / Swift |
| `scimark_sor` | [SciMark2](scimark2/README.md) 100×100 二维超松弛（500 轮） | `scimark_sor.xu` | Go / C / Rust / Swift |
| `scimark_lu` | [SciMark2](scimark2/README.md) 100×100 部分主元 LU 分解（30 轮） | `scimark_lu.xu` | Go / C / Rust / Swift |
| `scimark_sparse` | [SciMark2](scimark2/README.md) CSR 稀疏矩阵-向量乘（10000 阶 × 500 轮） | `scimark_sparse.xu` | Go / C / Rust / Swift |
| `scimark_fft` | [SciMark2](scimark2/README.md) 1024 点 Radix-2 复数 FFT（200 轮） | `scimark_fft.xu` | Go / C / Rust / Swift |
| `awfy_richards` | [AWFY](awfy/README.md) 6 任务 OS 调度模拟（50 轮） | `awfy_richards.xu` | Go / C / Rust / Swift |
| `awfy_json_parser` | [AWFY](awfy/README.md) 递归下降完整 JSON AST 解析（400 轮） | `awfy_json_parser.xu` | Go / C / Rust / Swift |
| `brainfuck_vm` | [进阶](awfy/README.md) Brainfuck 字节码解释器（4 轮 ~2070 万步） | `brainfuck_vm.xu` | Go / C / Rust / Swift |
| `regex_nfa` | [进阶](awfy/README.md) Thompson NFA 正则构造与匹配（6000 行 × 6 模式） | `regex_nfa.xu` | Go / C / Rust / Swift |
| `treap_ops` | [进阶](awfy/README.md) 节点池无旋转 Treap（12 万次操作） | `treap_ops.xu` | Go / C / Rust / Swift |
| `astar_maze` | [进阶](awfy/README.md) 60 张 81×81 迷宫最短路 A* 搜索 | `astar_maze.xu` | Go / C / Rust / Swift |
| `levenshtein_dp` | [进阶](awfy/README.md) Wagner-Fischer 双行编辑距离（400 对） | `levenshtein_dp.xu` | Go / C / Rust / Swift |
| `csv_aggregate` | [进阶](awfy/README.md) 10 轮 × 10 万行 CSV 定点哈希聚合 | `csv_aggregate.xu` | Go / C / Rust / Swift |
| `http_router_parse` | [Web/协议](web_proto/README.md) HTTP/1.1 请求解析、Trie 动态路由与 `%XX` 解码（12 万次） | `http_router_parse.xu` | Go / C / Rust / Swift |
| `websocket_frame` | [Web/协议](web_proto/README.md) RFC 6455 WebSocket 帧编码与掩码解码（80 帧 × 180 轮） | `websocket_frame.xu` | Go / C / Rust / Swift |
| `protobuf_varint` | [Web/协议](web_proto/README.md) Protobuf Varint/ZigZag 嵌套 RPC 批量编解码（20 万条） | `protobuf_varint.xu` | Go / C / Rust / Swift |
| `toml_config_parse` | [Web/协议](web_proto/README.md) TOML 多节配置文件词法解析（48 节 × 1000 轮） | `toml_config_parse.xu` | Go / C / Rust / Swift |
| `template_render` | [Web/协议](web_proto/README.md) HTML 模板字节码编译与 XSS 转义渲染（1 万页） | `template_render.xu` | Go / C / Rust / Swift |
| `hmac_pbkdf2` | [Web/协议](web_proto/README.md) FIPS SHA-256 + HMAC + PBKDF2-HMAC-SHA256 密钥派生 | `hmac_pbkdf2.xu` | Go / C / Rust / Swift |
| `btree_index` | [存储/检索](storage/README.md) Order-32 B+ 树索引插查与范围扫描 | `btree_index.xu` | Go / C / Rust / Swift |
| `lsm_compaction` | [存储/检索](storage/README.md) LSM-Tree 刷盘、多路堆归并压缩与 SSTable 查询 | `lsm_compaction.xu` | Go / C / Rust / Swift |
| `bm25_search` | [存储/检索](storage/README.md) CSR 倒排索引与定点 BM25 Top-10 检索 | `bm25_search.xu` | Go / C / Rust / Swift |
| `sql_query_exec` | [存储/检索](storage/README.md) 列式表过滤、Hash Join 与分组排序聚合 | `sql_query_exec.xu` | Go / C / Rust / Swift |
| `consistent_hash` | [存储/检索](storage/README.md) 虚拟节点一致性哈希环路由与 4 次扩缩容迁移 | `consistent_hash.xu` | Go / C / Rust / Swift |
| `wal_log_recovery` | [存储/检索](storage/README.md) 二进制 WAL 日志 CRC-32 校验与崩溃重放恢复 | `wal_log_recovery.xu` | Go / C / Rust / Swift |
| `expr_bytecode_vm` | [系统/工具](systems/README.md) 表达式词法分析、递归下降编译与栈字节码 VM | `expr_bytecode_vm.xu` | Go / C / Rust / Swift |
| `myers_diff` | [系统/工具](systems/README.md) Myers O(ND) 最短编辑脚本搜索与 trace 回溯 | `myers_diff.xu` | Go / C / Rust / Swift |
| `slab_allocator` | [系统/工具](systems/README.md) 6 档分级 Slab 内存分配器与整页回收 | `slab_allocator.xu` | Go / C / Rust / Swift |
| `timing_wheel` | [系统/工具](systems/README.md) 双层层级时间轮定时器调度、级联与取消 | `timing_wheel.xu` | Go / C / Rust / Swift |
| `lz4_block_codec` | [系统/工具](systems/README.md) LZ4 块级哈希匹配压缩与重叠拷贝解压 | `lz4_block_codec.xu` | Go / C / Rust / Swift |
| `utf8_text_norm` | [系统/工具](systems/README.md) 多语种 UTF-8 校验解码、全角/大小写折叠与空白规整 | `utf8_text_norm.xu` | Go / C / Rust / Swift |
| `raytrace_sphere` | [图形/物理](graphics_ai/README.md) 3D 球体光线追踪、阴影射线与 3 层镜面反射 | `raytrace_sphere.xu` | Go / C / Rust / Swift |
| `image_sobel_blur` | [图形/物理](graphics_ai/README.md) 512×512 图像 3×3 高斯模糊与 Sobel 边缘检测 | `image_sobel_blur.xu` | Go / C / Rust / Swift |
| `physics_collision` | [图形/物理](graphics_ai/README.md) 2D 空间哈希广相与定点弹性碰撞物理仿真 | `physics_collision.xu` | Go / C / Rust / Swift |
| `mlp_inference` | [AI/量化](graphics_ai/README.md) 3 层稠密神经网络 MLP 前向推理与 ReLU/Argmax | `mlp_inference.xu` | Go / C / Rust / Swift |
| `kmeans_cluster` | [AI/量化](graphics_ai/README.md) 8 维 K-Means 聚类迭代（8192 点 × 16 簇 × 25 轮） | `kmeans_cluster.xu` | Go / C / Rust / Swift |
| `order_book_match` | [AI/量化](graphics_ai/README.md) 金融限价订单簿价格-时间优先撮合与 O(1) 撤单 | `order_book_match.xu` | Go / C / Rust / Swift |
| `x25519_dh` | [现代密码](graphics_ai/README.md) RFC 7748 Curve25519 / X25519 蒙哥马利阶梯密钥交换 | `x25519_dh.xu` | Go / C / Rust / Swift |
| `parallel_mapreduce` | [并发流水线](graphics_ai/README.md) 8 Worker 并发 MapReduce 通道扇出与归约 | `parallel_mapreduce.xu` | Go / Rust |

规则：同算法直译，`int` = i64，计数用 `while`，stdout checksum 必须逐字节一致。不是各语言最快写法（Go 不用 `for range` 特化、C 不做手写 SIMD）。跨语言测量方法见[根 README](../../README.md#测量口径)：整程序 wall、best+median、峰值 RSS + CPU(user+sys)、可选 `--discard-first`。结果仅覆盖这些负载与所测环境。

- Xu 运行时对拍：`scripts/bench_runtime.sh` / `make runtime`（同一 hosted 产品编译器分别以 `--no-opt` 与默认优化编译，核对输出；耗时取 best-of，默认 5 次，可用 `--iters=N` 调整）。
- 优化模式：`scripts/bench_opt_full.sh` / `make opt-full` 对比默认优化和 `--no-opt` 的运行、资源与编译时间。用 `--digest` 查看上次结果。门禁 `make opt-levels ARGS="--check"` 检查 stdout、超时和墙钟与 CPU 时间。
- 优化诊断：`python3 scripts/opt_stage_bisect.py --bench=iface_sum` 比较默认优化与 `--no-opt`，支持优化阶段转储的编译器可进一步定位。
- 跨语言：`make crosslang`（通过 hosted seed resolver 选择产品编译器，再由 hermetic wrapper 编译 Xu 负载；此入口不执行自举固定点检查）
  - 直接运行脚本时也使用同一 resolver；默认从 Xu 仓库的 `bin/xu` 或 hosted snapshot 选择，`--xu=PATH` 可指定另一个 hosted 产品编译器
  - `--quick` 省去对照语言的调试档和编译时间；Xu 使用默认优化，Clang（主机缺失时 GCC）、rustc 的 O1/O2/O3 仍全部参与（安静机器；热机会偏慢）
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
