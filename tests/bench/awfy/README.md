# 批次 C 进阶基准题接入说明

本目录记录批次 C 引入的 8 项进阶跨语言负载的上游出处、许可协议与确定性校验口径，每题均提供 Xu / Go / C / Rust / Swift 五语言同算法实现。

| 注册名 | 上游来源 / 灵感 | 许可 | 度量面与校验口径 |
|---|---|---|---|
| `awfy_richards` | [smarr/are-we-fast-yet](https://github.com/smarr/are-we-fast-yet) (`Richards`) | MIT | 6 任务 OS 调度模拟 × 50 轮，输出总入队与挂起次数（`1162300` / `464850`） |
| `awfy_json_parser` | [smarr/are-we-fast-yet](https://github.com/smarr/are-we-fast-yet) (`Json`) | MIT | 递归下降完整 JSON 解析构建 AST × 400 轮，输出节点总数与结构校验和 |
| `brainfuck_vm` | [kostya/benchmarks](https://github.com/kostya/benchmarks) (`brainfuck`) | MIT | 平铺字节码解释器执行自包含 BF 程序（4 轮约 2070 万步），输出字节数与 Fletcher-16 校验和 |
| `regex_nfa` | 经典 Thompson NFA 构造与同步状态集匹配 | 自研 (MIT) | 6000 行混合日志文本 × 6 条正则模式匹配，输出总命中行与加权校验和 |
| `treap_ops` | [frol/completely-unscientific-benchmarks](https://github.com/frol/completely-unscientific-benchmarks) (`treap`) | MIT | 节点池无旋转 Treap `split`/`merge` 12 万次混合操作，输出命中数、校验和与最终大小 |
| `astar_maze` | [kostya/LangArena](https://github.com/kostya/LangArena) (`maze` A\*) | MIT | 60 张 81×81 迷宫最短路 A\* 搜索，输出最短步数之和与多项式校验和 |
| `levenshtein_dp` | [kostya/benchmarks](https://github.com/kostya/benchmarks) (`levenshtein`) | MIT | 400 对长度 120..219 字符串 Wagner-Fischer 双行滚动 DP，输出距离和与校验和 |
| `csv_aggregate` | 1BRC 启发式流解析聚合（定点整数十分位） | 自研 (MIT) | 10 轮 × 10 万行 CSV 流字节扫描 + 开放定址哈希表聚合 64 站点 `min/max/sum/count` |
