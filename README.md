# Xu 基准与横测

Xu 基准工具与负载的独立仓库：选定的语言能力、标准库、优化档、编译时间、
Benchmarks Game、Clang 差距、资源曲线与 stdout 金标。

默认与 `xu` 放在同级目录；可通过 `XU_ROOT=/path/to/xu` 选择编译器源码仓库。
编译器与标准库仍由 Xu 仓库构建，本仓库维护负载、对照实现和测量方法。
Xu 负载通过 Xu 的 hosted seed resolver 选择产品编译器，并通过 hermetic
wrapper 编译；跨语言对照还需要相应语言的工具链。运行时对拍比较同一
编译器的 O0 与默认优化结果。这些负载的结果仅代表所测输入与环境。

从本仓库根目录执行以下命令。需要 Make、Python 3、Bash；`make test` 另需
`pytest`（可在虚拟环境中用 `python3 -m pip install pytest` 安装）。
实际编译 Xu 负载前，须在 `XU_ROOT` 中准备可执行的 hosted 产品编译器
（通常为 `bin/xu`；参见 [Xu 仓库说明](https://github.com/xulang-org/xu)）；列出负载和运行
Python 测试不需要先构建 Xu。跨语言测试按已安装的 Clang、Rust、Go、
Swift 等工具链运行可用对照，报告中的缺失项不能视为测量结果。

```sh
export XU_ROOT="${XU_ROOT:-$(cd ../xu && pwd)}"
make list
make crosslang ARGS="--quick --benches=loop_sum --iters=1 --sample-ms=0"
make game ARGS="--verify-only --benches=nbody"
bash scripts/bench_stdlib.sh --benches=rand_read --iters=1
make opt-levels ARGS="--quick --check"
python3 scripts/bench_clang_gap_manifest.py
make test
```

Windows 原生 Python 的性能入口会通过 Git for Windows Bash 调用相同的隔离编译包装器，
保留参数边界和编译器退出状态。请安装 Git for Windows，并确保 Bash 中的 `python3`
指向可用的 Python 3 解释器。可从 PowerShell 直接运行：

```powershell
$env:XU_ROOT = (Resolve-Path ../xu).Path
python scripts/bench_opt_levels.py --xu ../xu/bin/xu.exe --quick --check
python scripts/bench_stdlib.py --xu ../xu/bin/xu.exe --iters=7 --discard-first
python -m pytest tests scripts/test_bench_game.py
```

Windows 的 Xu 编译 wall time 包含隔离包装器开销。优化档报告中的编译 CPU/RSS
显示为 `nan`（不可用）：Windows 进程计数只覆盖 Bash 本身，不能将其冒充编译器子进程。
已生成的 Xu 程序仍直接执行，运行 CPU/RSS 按目标进程采集。
优化档采样在建立 O1 基线前使用 60 秒超时，随后沿用相对 O1 的期限；首轮预热死锁
会保留为失败样本，并继续检查其他配置。
标准库文件 I/O 负载在临时目录创建或文件写入失败时返回非零状态，避免将错误标记
误存为成功的性能样本。

更多负载说明见 [套件索引](tests/bench/README.md)。

`http_concurrent` 使用 16 个 worker，各执行 200 次自环回 HTTP 请求。
每次请求建立新 TCP 连接，校验响应正文和固定校验和；Xu、Go、Rust 提供对照实现。
Go 使用 `net/http`，Rust 使用标准库线程与最小 HTTP 服务，结果包含连接、调度和协议开销。
该负载尚未进入官网统一多平台测量，不能混入已有正式数据的性能比值。
Windows 的临时 TCP 端口会被 `TIME_WAIT` 保留。每次启动该负载前，工具读取实际 IPv4
动态端口范围与 TCP 表，等待足够容纳 3200 次新连接及 1024 个余量；各语言使用同一准入
策略。等待最多 300 秒并单独记录，不计入目标 wall/CPU/RSS，也不修改系统设置。完整
矩阵因此可能包含数分钟的冷却；连接负载与性能阈值保持原值。

`reports/`、曲线和运行产物仅本机保留，不提交。原语言仓库的 `docs/`
评测记录留在原处；需要旧基线时显式传入其路径。
`make compile` 默认要求 `reports/bench_compile.baseline.txt`，可以用
`BENCH_BASELINE=/path/to/baseline.txt` 指定经过校准的基线。

## 测量口径

跨语言测试默认取七次独立进程运行的中位数；可用 `--discard-first`
额外执行并丢弃一次预跑。核对 stdout
后才接受结果。wall time 和 CPU time 来自直接执行的进程。

Linux 的 `wait4.ru_maxrss` 会保留启动器在 exec 前的内存峰值，不能直接
当作目标程序的 RSS。Linux 因此另行执行相同命令：原生 C 采样器在目标
exec 完成后、退出前读取该地址空间的 `VmHWM`，并以 `smaps_rollup` 的
当前 RSS 补齐短进程计数。每次 RSS 重跑都核对退出状态；跨语言负载还
要求 stdout/stderr 与计时运行一致。采样器构建及 ptrace 开销不计入
wall/CPU time。Linux 需要可用的 `cc`、`clang` 或 `gcc` 及 ptrace 权限；
采样不可用时失败，不回退到失真的旧数值。此协议记为
`linux-post-exec-vmhwm-v1`，旧 Linux RSS 结果需要重新测量。

macOS 使用 `wait4` 的峰值 RSS，Windows 使用 `PeakWorkingSetSize`。
RSS 描述目标进程本身，不合计子进程；原生负载只允许一次 exec。
实时 RSS 曲线来自计时进程的实际轮询，不用另一次运行的峰值补点。
不同负载的资源范围只用于描述，不能按范围下限判定某语言整体最优。

## 许可

本仓库自有工具、负载与对照实现采用 [MIT 许可证](LICENSE)。第三方材料保留
其原有版权与许可；Benchmarks Game 金标输出的来源、校验值和上游许可见
[golden 说明](tests/bench/game/golden/README.md)。

### 六平台发布门禁

横测的 Linux、macOS、Windows × ARM64/x86_64 六个作业均为必需项。任一作业失败时不聚合发布；聚合后还会核对六个平台、相同的用例集合、有效 Xu 测量及同一源码提交。失败或缺失的架构不能成为一份成功的完整横测。CPU 时间受系统计时分辨率影响，不以零值单独判定失败。
