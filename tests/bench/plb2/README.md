# PLB2 基准题接入

参考来源：[attractivechaos/plb2](https://github.com/attractivechaos/plb2)（CC0 1.0 Public Domain）。
本目录记录该批 3 项跨语言移植负载的算法来源与确定性校验口径，每题均提供 Xu / Go / C / Rust / Swift 五语言同算法实现。

| 注册名 | 上游原型 | 度量面 | 规模与校验方式 |
|---|---|---|---|
| `plb2_nqueen` | `nqueen` | 位运算迭代回溯（15 皇后） | `N = 15`，输出精确解总数 `2279184` |
| `plb2_sudoku` | `sudoku` (`kudoku`) | 精确覆盖约束传播 + MRV 回溯 | 10 道高难度唯一解数独 × 20 轮，输出解数字多项式校验和 |
| `plb2_bedcov` | `bedcov` (`cgranges`) | 隐式区间树索引与重叠查询 | 200,000 目标区间 + 200,000 查询区间，输出总命中数与重叠长度和 |
