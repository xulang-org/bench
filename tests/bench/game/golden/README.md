# Benchmarks Game 金标输出来源

这些文件来自 Computer Language Benchmarks Game 的官方输出下载；它们作为
`scripts/bench_game.py` 的小 N 正确性基线，不是本仓库的性能测量结果。
下表链接对应官方题目说明中的 output file。2026-10-27 重新下载后，六个文件
均与本目录已有文件逐字节一致；保留原始字节（包括换行和 PBM 二进制内容）。

| 本地文件 | verify N | 官方说明 | 官方输出下载 | SHA-256 |
|---|---:|---|---|---|
| [nbody-output.txt](nbody-output.txt) | 1000 | [n-body](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/nbody.html) | [download](https://benchmarksgame-team.pages.debian.net/benchmarksgame/download/nbody-output.txt) | `76de83d6d51a74f82828547423f516e7815cfe8cfea6290a2831aa173f806de7` |
| [fannkuchredux-output.txt](fannkuchredux-output.txt) | 7 | [fannkuch-redux](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/fannkuchredux.html) | [download](https://benchmarksgame-team.pages.debian.net/benchmarksgame/download/fannkuchredux-output.txt) | `2dc0a3cd4a547ba69389f97f3b447bd4d487fe6216c3cacd2f9bf8c908dc127f` |
| [spectralnorm-output.txt](spectralnorm-output.txt) | 100 | [spectral-norm](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/spectralnorm.html) | [download](https://benchmarksgame-team.pages.debian.net/benchmarksgame/download/spectralnorm-output.txt) | `a95e11fa07f7b196ef488e73f67afbbbc16cf6a2c6de5f8d54ea49821fe604e6` |
| [mandelbrot-output.txt](mandelbrot-output.txt) | 200 | [mandelbrot](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/mandelbrot.html) | [download](https://benchmarksgame-team.pages.debian.net/benchmarksgame/download/mandelbrot-output.txt) | `97610473750700638fc63d13cfa49d339b67c18e7f26b3f9c9acb61e746472d5` |
| [fasta-output.txt](fasta-output.txt) | 1000 | [fasta](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/fasta.html) | [download](https://benchmarksgame-team.pages.debian.net/benchmarksgame/download/fasta-output.txt) | `62d1e8d0df7938d2aefda9a37887e0389231ea72c099c29a51afb6edca1bdc73` |
| [binarytrees-output.txt](binarytrees-output.txt) | 10 | [binary-trees](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/binarytrees.html) | [download](https://benchmarksgame-team.pages.debian.net/benchmarksgame/download/binarytrees-output.txt) | `b7f92c56b5d8aeb0a4d698842d1d87a57b4909865c3c84e5e10313e16663c3cb` |

## 上游许可

这些第三方输出保留上游许可，不由仓库根 MIT 许可证重新授权。
以下文本来自官方 [Revised BSD license](https://benchmarksgame-team.pages.debian.net/benchmarksgame/license.html)
页面（2026-10-27 核对），保留上游版权年份和条款。

```text
Copyright © 2004-2008 Brent Fulgham, 2005-2025 Isaac Gouy

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

3. Neither the name "The Computer Language Benchmarks Game" nor the name "The Benchmarks Game" nor the name "The Computer Language Shootout Benchmarks" nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```
