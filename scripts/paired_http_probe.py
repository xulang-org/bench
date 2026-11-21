"""Paired macOS diagnosis for the fixed http_concurrent workload."""
import json
import os
from pathlib import Path
import select
import statistics
import subprocess
import sys
import time

from bench_rusage import run_one

BENCH = Path(__file__).resolve().parents[1]
OUT = Path.cwd() / "out"
EXPECTED = b"3200\n35945209188\n"


def generate_sources():
    original = (BENCH / "tests/bench/http_concurrent.xu").read_text()
    before, main = original.split("fn main() int {")
    before = before.replace("#net\n", "#net\n#os\n", 1)
    addr = '    args := os.args()\n    if args.len != 2 { << 2 }\n    addr := args[1]\n'
    client = main.split("    xu serve(lfd)\n", 1)[1]
    (OUT / "client.xu").write_text(before + "fn main() int {\n" + addr + client)
    server = '''
    lfd := net.listen(addr + "") or (err) { << 3 }
    println("ready")
    serve(lfd)
    << 0
}
'''
    (OUT / "server.xu").write_text(before + "fn main() int {\n" + addr + server)
    go = (BENCH / "tests/bench/cross/http_concurrent.go").read_text()
    prefix, main = go.split("func main() {")
    workers = main[main.index("\tout := make(chan uint32, conns)"):]
    modes = '''
    addr := os.Args[2]
    if os.Args[1] == "server" {
        ln, err := net.Listen("tcp", addr)
        if err != nil { panic(err) }
        fmt.Println("ready")
        if err := http.Serve(ln, http.HandlerFunc(handler)); err != nil { panic(err) }
        return
    }
'''
    (OUT / "peer.go").write_text(prefix + "func main() {\n" + modes + workers)


def add_counters():
    file = Path("dev/src/net/http/server.xu")
    source = file.read_text()
    before, rest = source.split("fn accept_ready_event_set(", 1)
    accept, rest = rest.split("fn serve_listener_root_event_set(", 1)
    accept = accept.replace("options &ServerOptions) bool", "options &ServerOptions, probes $&int) bool", 1)
    accept = accept.replace("        ready := os.socket_poll", "        *probes = *probes + 1\n        ready := os.socket_poll", 1)
    accept = accept.replace("            _ := os.socket_poll", "            *probes = *probes + 1\n            _ := os.socket_poll", 1)
    rest = rest.replace("$&listening_watch, &options)", "$&listening_watch, &options, $&probes)")
    anchor = "    $pending_wakes := 0\n"
    rest = rest.replace(anchor, anchor + "    $probes := 0\n    $waits := 0\n    $completed := 0\n", 1)
    rest = rest.replace("        batch := events.wait", "        waits += 1\n        batch := events.wait", 1)
    rest = rest.replace("            ready := os.socket_poll", "            probes += 1\n            ready := os.socket_poll", 1)
    rest = rest.replace("            _ := os.socket_poll", "            probes += 1\n            _ := os.socket_poll", 1)
    anchor = "            pending_wakes -= 1\n"
    report = '''
            completed += 1
            if completed == 3200 {
                println(probes)
                println(waits)
                println(completed)
            }
'''
    assert rest.count(anchor) == 1 and rest.count("$&listening_watch, &options, $&probes)") == 2
    file.write_text(before + "fn accept_ready_event_set(" + accept + "fn serve_listener_root_event_set(" + rest.replace(anchor, anchor + report, 1))


def wait_for_capacity():
    low, high = [int(subprocess.check_output(["sysctl", "-n", "net.inet.ip.portrange." + k]))
                 for k in ("first", "last")]
    start = time.monotonic()
    while time.monotonic() - start < 180:
        live = set()
        table = subprocess.check_output(["netstat", "-an", "-p", "tcp"], text=True)
        for line in table.splitlines():
            cols = line.split()
            if len(cols) < 6 or not cols[0].startswith("tcp"):
                continue
            for address in cols[3:5]:
                host, _, port = address.rpartition(".")
                if host == "127.0.0.1" and port.isdecimal() and low <= int(port) <= high:
                    live.add(int(port))
        if high - low + 1 - len(live) >= 4224:
            return
        time.sleep(2)
    raise TimeoutError("loopback port capacity")


def record(name, data):
    with (OUT / name).open("a") as f:
        print(json.dumps(data), file=f, flush=True)
    print(json.dumps(data), flush=True)


def invoke(case, port, trace=False):
    wait_for_capacity()
    addr = f"127.0.0.1:{port}"
    server = None
    if isinstance(case, str):
        command = [str(OUT / case)]
    else:
        server_name, client = case
        server_cmd = [str(OUT / server_name)] + (["server"] if server_name == "go-peer" else []) + [addr]
        command = [str(OUT / client)] + (["client"] if client == "go-peer" else []) + [addr]
        server = subprocess.Popen(server_cmd, stdout=subprocess.PIPE)
    try:
        if server:
            if not select.select([server.stdout], [], [], 10)[0] or server.stdout.readline().strip() != b"ready":
                raise RuntimeError(f"server did not start: {case}")
        sample = run_one(command, timeout_s=60)
        if sample.returncode or sample.stdout != EXPECTED:
            raise RuntimeError(f"{case}: {sample.returncode}, {sample.stdout!r}, {sample.stderr!r}")
        if trace:
            if not select.select([server.stdout], [], [], 8)[0]:
                raise RuntimeError("missing event-loop counters")
            probes, waits, wakes = [int(server.stdout.readline()) for _ in range(3)]
            return dict(probes=probes, waits=waits, finished_notifications=wakes)
        return dict(wall_ms=sample.wall_s*1000, cpu_ms=sample.cpu_s*1000, rss_mib=sample.max_rss_mib)
    finally:
        if server:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()


def measure():
    original = ["base-original", "dev-original", "go-original"]
    peers = [("base-server", "go-peer"), ("dev-server", "go-peer"),
             ("go-peer", "dev-client"), ("go-peer", "go-peer")]
    port = 28000
    for group in (original, peers):
        results = {str(case): [] for case in group}
        for index in range(7):
            order = group[index % len(group):] + group[:index % len(group)]
            for case in order:
                port += 1
                sample = invoke(case, port)
                record("samples.jsonl", dict(round=index+1, case=case, **sample))
                results[str(case)].append(sample)
        for case, samples in results.items():
            record("summary.jsonl", dict(case=case, **{
                key: statistics.median([s[key] for s in samples]) for key in samples[0]
            }))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "sources":
        generate_sources()
    elif mode == "measure":
        measure()
    elif mode == "counters":
        add_counters()
    elif mode == "trace":
        for i in range(3):
            record("trace.jsonl", invoke(("count-server", "go-peer"), 29000 + i, trace=True))
    else:
        raise SystemExit(mode)
