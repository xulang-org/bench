"""Darwin short-connection readiness diagnostics on a dedicated CI runner."""
import json
import re
import select
import signal
import struct
import subprocess
import sys
import time
from pathlib import Path
from statistics import median, quantiles

from bench_rusage import run_one
from paired_http_probe import OUT, EXPECTED, generate_sources, record, wait_for_capacity


def configure():
    generate_sources()
    directory = Path("dev/src/runtime/core")
    chan = directory / "chan.xu"
    source = chan.read_text().replace("const S_SIZE = 96", "const S_SIZE = 160")
    before = "    st(s + S_DRAIN, 1)"
    assert source.count(before) == 1
    source = source.replace(before, "    for i in 0:8 { print_int(2, ld(s + 96 + 8 * i), true) }\n" + before)
    chan.write_text(source)
    host = directory / "host.xu"
    src = host.read_text()
    start, body = src.split("fn host_poll_task(", 1)
    body = body.replace("    $deadline := 0", "    s := sched()\n    if events == 1 { st(s + 96, ld(s + 96) + 1) }\n    $deadline := 0", 1)
    body = body.replace("        if r != 0 {", """        if events == 1 {
            st(s + 104, ld(s + 104) + 1)
            if r == 0 { st(s + 112, ld(s + 112) + 1) }
        }
        if r != 0 {""", 1)
    body = body.replace("        if task_io_yield_kind(false) {", """        yielded_at := host_now_ns()
        can_wait := task_io_yield_kind(false)
        if events == 1 {
            st(s + 120, ld(s + 120) + 1)
            st(s + 128, ld(s + 128) + host_now_ns() - yielded_at)
        }
        if can_wait {""", 1)
    body = body.replace("            r2 := host_poll_ms(fd, events, pms)", """            wait_at := host_now_ns()
            r2 := host_poll_ms(fd, events, pms)
            if events == 1 {
                st(s + 136, ld(s + 136) + 1)
                if r2 == 0 { st(s + 144, ld(s + 144) + 1) }
                st(s + 152, ld(s + 152) + host_now_ns() - wait_at)
            }""", 1)
    host.write_text(start + "fn host_poll_task(" + body)
    client = (OUT / "client.xu").read_text()
    client = client.replace("seq int) string {\n    fd := net.dial_ns", "seq int, stamp $&int) string {\n    fd := net.dial_ns")
    client = client.replace("        if !ok {", "        *stamp = wall_time_ns()\n        if !ok {")
    client = client.replace("    $failed := false", "    $stamps := []int{}\n    $failed := false")
    client = client.replace('        body := fetch(addr + "", seq)', '        $stamp := 0\n        body := fetch(addr + "", seq, $&stamp)\n        stamps.push(stamp)')
    client = client.replace("    if failed {", """    $report := ""
    for j in 0:stamps.len {
        report.push_str("R " + strconv.itoa(base + j) + " " + strconv.itoa(stamps[j]) + "\\n")
    }
    eprintln(report)
    if failed {""")
    (OUT / "diagnostic.xu").write_text(client)


def response_arrivals(pcap, port):
    raw = pcap.read_bytes()
    formats = {b"\xd4\xc3\xb2\xa1": ("<", 1000), b"\xa1\xb2\xc3\xd4": (">", 1000),
               b"\x4d\x3c\xb2\xa1": ("<", 1), b"\xa1\xb2\x3c\x4d": (">", 1)}
    endian, scale = formats[raw[:4]]
    link = struct.unpack_from(endian + "I", raw, 20)[0] & 0xffff
    if link != 0:
        raise RuntimeError(f"expected DLT_NULL, got {link}")
    found = {}
    pos = 24
    while pos < len(raw):
        sec, frac, length, _ = struct.unpack_from(endian + "4I", raw, pos)
        frame = raw[pos + 16:pos + 16 + length]
        pos += 16 + length
        if len(frame) < 44 or frame[4] >> 4 != 4 or frame[13] != 6:
            continue
        tcp = 4 + (frame[4] & 15) * 4
        if int.from_bytes(frame[tcp:tcp+2], "big") != port:
            continue
        payload = frame[tcp + (frame[tcp+12] >> 4) * 4:]
        m = re.search(rb"pong-([0-9]+)\n", payload)
        if m:
            found.setdefault(int(m[1]), sec * 10**9 + frac * scale)
    return found


def diagnose(index):
    wait_for_capacity()
    port = 32500 + index
    addr = f"127.0.0.1:{port}"
    capture = OUT / "response.pcap"
    server = subprocess.Popen([OUT / "go-peer", "server", addr], stdout=subprocess.PIPE)
    try:
        if not select.select([server.stdout], [], [], 10)[0] or server.stdout.readline().strip() != b"ready":
            raise RuntimeError("server failed to start")
        with (OUT / "tcpdump.log").open("w+") as log:
            dumper = subprocess.Popen(["sudo", "-n", "tcpdump", "-i", "lo0", "-y", "NULL", "-n", "-B", "4096",
                                       "-s", "1024", "-U", "-w", str(capture), "tcp", "src", "port", str(port)], stderr=log)
            try:
                for _ in range(100):
                    if dumper.poll() is not None:
                        raise RuntimeError((OUT / "tcpdump.log").read_text())
                    if "listening on" in (OUT / "tcpdump.log").read_text() or capture.exists() and capture.stat().st_size >= 24:
                        break
                    time.sleep(.1)
                else:
                    raise TimeoutError("capture not ready")
                sample = run_one([str(OUT / "diagnostic"), addr], timeout_s=60)
                time.sleep(1)
            finally:
                if dumper.poll() is None:
                    subprocess.run(["sudo", "-n", "pkill", "-INT", "-f", "^.*tcpdump .*" + str(port) + "$"], check=False)
                    dumper.wait(timeout=10)
        err = sample.stderr.decode()
        if sample.returncode or sample.stdout != EXPECTED:
            raise ValueError(f"{sample.returncode} {sample.stdout} {err[-300:]}")
        stamps = {int(i):int(t) for i,t in re.findall(r"^R (\d+) (\d+)$", err, re.M)}
        counts = [int(s) for s in err.splitlines() if s.isdecimal()]
        if len(counts) != 8 or len(stamps) != 3200:
            raise ValueError(f"unexpected telemetry {len(counts)}, {len(stamps)}, {err[-300:]}")
        labels = ["read_calls","zero_probes","empty_probes","yields","yield_ns","one_ms_polls","one_ms_expired","one_ms_elapsed_ns"]
        record("counters.jsonl", dict(round=index+1, **dict(zip(labels,counts))))
        arrivals = response_arrivals(capture, port)
        delays = [(stamps[seq]-arrivals[seq])/1000 for seq in stamps.keys() & arrivals.keys()]
        if len(delays) < 3168 or min(delays) < -100:
            raise ValueError(f"packet correlation: {len(delays)}, {min(delays, default=0)}")
        record("arrival.jsonl", dict(round=index+1, correlated=len(delays), median_us=median(delays),
                                     p95_us=quantiles(delays,n=100)[94], mean_us=sum(delays)/len(delays)))
    finally:
        server.terminate()
        server.wait(timeout=10)
        capture.unlink(missing_ok=True)


if __name__ == "__main__":
    if sys.argv[1] == "configure":
        configure()
    else:
        for i in range(3):
            diagnose(i)
