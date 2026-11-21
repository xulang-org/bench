"""Time the original client operations against the same independent Go service."""
from pathlib import Path
import json
import select
import subprocess

from bench_rusage import run_one
from paired_http_probe import EXPECTED, OUT, generate_sources, record, wait_for_capacity


def sources():
    generate_sources()
    xu = (OUT / "client.xu").read_text()
    xu = xu.replace("fn fetch(addr string, seq int) string {", """
struct PhaseTimes { dial int; write int; read int; close int; total int }
fn fetch(addr string, seq int, stats $&PhaseTimes) string {
    begin := now_ns()
""".replace("; ", "\n    "))
    xu = xu.replace("    req := ", "    stats.dial += now_ns() - begin\n    req := ", 1)
    xu = xu.replace("    net.conn_write(", "    write_begin := now_ns()\n    net.conn_write(", 1)
    xu = xu.replace('    $buf := ""', '    stats.write += now_ns() - write_begin\n    $buf := ""', 1)
    xu = xu.replace('        part = net.conn_read', '        read_begin := now_ns()\n        part = net.conn_read')
    xu = xu.replace('        if !ok {', '        stats.read += now_ns() - read_begin\n        if !ok {')
    xu = xu.replace("    net.conn_close(fd) or (err) { << body }", """    close_begin := now_ns()
    net.conn_close(fd) or (err) { << body }
    end := now_ns()
    stats.close += end - close_begin
    stats.total += end - begin""")
    xu = xu.replace("    $failed := false", "    $stats := PhaseTimes{dial: 0, write: 0, read: 0, close: 0, total: 0}\n    $failed := false")
    xu = xu.replace('body := fetch(addr + "", seq)', 'body := fetch(addr + "", seq, $&stats)')
    fields = ["dial", "write", "read", "close", "total"]
    line = ' + " " + '.join("strconv.itoa(stats." + f + ")" for f in fields)
    xu = xu.replace("    if failed {", "    eprintln(" + line + ")\n    if failed {")
    (OUT / "xu-phases.xu").write_text(xu)

    go = (OUT / "peer.go").read_text().replace('import (', 'import (\n    "time"', 1)
    go = go.replace("h := uint32(2166136261)", "h := uint32(2166136261)\n var dial, write, read, closeTime, total int64")
    go = go.replace("conn, err := net.Dial", "begin := time.Now()\n conn, err := net.Dial")
    go = go.replace('req := "GET', 'dial += time.Since(begin).Nanoseconds()\n req := "GET')
    go = go.replace("if _, err := conn.Write", "wr := time.Now()\n if _, err := conn.Write")
    go = go.replace("resp, err := io.ReadAll(conn)", "write += time.Since(wr).Nanoseconds()\n rd := time.Now()\n resp, err := io.ReadAll(conn)\n read += time.Since(rd).Nanoseconds()\n cl := time.Now()")
    go = go.replace("conn.Close()", "conn.Close()\n closeTime += time.Since(cl).Nanoseconds()")
    go = go.replace("if body != expectedBody", "total += time.Since(begin).Nanoseconds()\n if body != expectedBody")
    go = go.replace("out <- h", "fmt.Fprintln(os.Stderr, dial, write, read, closeTime, total)\n out <- h")
    (OUT / "go-phases.go").write_text(go)


def measure():
    keys = ["dial", "write", "read", "close", "total"]
    for i in range(7):
        langs = ["xu", "go"] if i % 2 == 0 else ["go", "xu"]
        for j, lang in enumerate(langs):
            wait_for_capacity()
            addr = f"127.0.0.1:{31000 + 2*i + j}"
            server = subprocess.Popen([OUT / "go-peer", "server", addr], stdout=subprocess.PIPE)
            try:
                if not select.select([server.stdout], [], [], 10)[0] or server.stdout.readline().strip() != b"ready":
                    raise RuntimeError("Go server did not start")
                command = [str(OUT / (lang + "-phases"))] + (["client"] if lang == "go" else []) + [addr]
                sample = run_one(command, timeout_s=60)
                if sample.stdout != EXPECTED or sample.returncode:
                    raise RuntimeError(f"{command}: {sample.stdout!r} {sample.stderr!r}")
                rows = [list(map(int, line.split())) for line in sample.stderr.splitlines()]
                if len(rows) != 16 or any(len(row) != 5 or min(row) < 0 or sum(row[:4]) > row[4] for row in rows):
                    raise RuntimeError(f"invalid worker telemetry: {rows}")
                per_request_us = {key: sum(row[k] for row in rows) / (3200 * 1000) for k, key in enumerate(keys)}
                record("phases.jsonl", dict(round=i+1, client=lang, wall_ms=sample.wall_s*1000, per_request_us=per_request_us))
            finally:
                server.terminate()
                server.wait(timeout=10)


if __name__ == "__main__":
    import sys
    if sys.argv[1] == "sources":
        sources()
    else:
        measure()
