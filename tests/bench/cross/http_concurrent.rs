use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::mpsc;
use std::thread;

// HTTP high-concurrency throughput over a loopback server.
//
// 16 concurrent workers x 200 requests. Every request opens a fresh TCP
// connection and sends "Connection: close", so all languages pay the same
// connect/teardown cost and no keep-alive reuse can hide server differences.
//
// The server side uses each language's idiomatic HTTP server (Go: net/http,
// Rust: std::net, Xu: net/http). The client side is raw TCP on every
// language so the wire traffic is identical.
//
// stdout: completed request count, then the order-independent checksum
// (sum of the per-worker FNV-1a-32 hashes over the response bodies).

const CONNS: usize = 16;
const REQ_PER_CONN: usize = 200;

fn expected_body(seq: usize) -> String {
    format!("pong-{}\n", seq)
}

fn fnv_update(mut h: u32, body: &[u8]) -> u32 {
    for &b in body {
        h ^= b as u32;
        h = h.wrapping_mul(16777619);
    }
    h
}

fn find(haystack: &[u8], needle: &[u8]) -> Option<usize> {
    if needle.len() > haystack.len() {
        return None;
    }
    for i in 0..=(haystack.len() - needle.len()) {
        if &haystack[i..i + needle.len()] == needle {
            return Some(i);
        }
    }
    None
}

fn handle(mut conn: TcpStream) {
    let mut buf = [0u8; 1024];
    let mut acc: Vec<u8> = Vec::new();
    let mut header_end: Option<usize> = None;
    while header_end.is_none() {
        let n = match conn.read(&mut buf) {
            Ok(0) => break,
            Ok(n) => n,
            Err(_) => return,
        };
        acc.extend_from_slice(&buf[..n]);
        header_end = find(&acc, b"\r\n\r\n");
    }
    let header_end = match header_end {
        Some(p) => p,
        None => return,
    };
    let head = String::from_utf8_lossy(&acc[..header_end]).to_string();
    let mut parts = head.split_whitespace();
    let _method = parts.next();
    let path = parts.next().unwrap_or("");
    let seq: usize = path
        .strip_prefix("/r/")
        .unwrap_or("")
        .parse::<usize>()
        .unwrap_or(0);
    let body = expected_body(seq);
    let resp = format!(
        "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
        body.len(),
        body
    );
    let _ = conn.write_all(resp.as_bytes());
    let _ = conn.flush();
}

fn worker(addr: &str, base: usize, out: mpsc::Sender<u32>) {
    let mut h: u32 = 2166136261;
    for i in 0..REQ_PER_CONN {
        let seq = base + i;
        let mut conn = match TcpStream::connect(addr) {
            Ok(c) => c,
            Err(e) => {
                eprintln!("dial: {}", e);
                std::process::exit(1);
            }
        };
        let req = format!(
            "GET /r/{} HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n",
            seq
        );
        if conn.write_all(req.as_bytes()).is_err() {
            eprintln!("write failed");
            std::process::exit(1);
        }
        let mut resp = Vec::new();
        if conn.read_to_end(&mut resp).is_err() {
            eprintln!("read failed");
            std::process::exit(1);
        }
        drop(conn);
        let idx = match find(&resp, b"\r\n\r\n") {
            Some(p) => p,
            None => {
                eprintln!("no header end");
                std::process::exit(1);
            }
        };
        let body = &resp[idx + 4..];
        let want = expected_body(seq);
        if body != want.as_bytes() {
            eprintln!("body mismatch");
            std::process::exit(1);
        }
        h = fnv_update(h, body);
    }
    let _ = out.send(h);
}

fn main() {
    let ln = TcpListener::bind("127.0.0.1:0").expect("listen failed");
    let port = ln.local_addr().expect("local_addr failed").port();
    let addr = format!("127.0.0.1:{}", port);

    thread::spawn(move || {
        for stream in ln.incoming() {
            match stream {
                Ok(s) => {
                    thread::spawn(move || {
                        handle(s);
                    });
                }
                Err(_) => break,
            }
        }
    });

    let (tx, rx) = mpsc::channel::<u32>();
    for w in 0..CONNS {
        let a = addr.clone();
        let t = tx.clone();
        thread::spawn(move || {
            worker(&a, w * REQ_PER_CONN, t);
        });
    }
    drop(tx);

    let mut sum: u64 = 0;
    for _ in 0..CONNS {
        sum += rx.recv().expect("worker dropped") as u64;
    }
    println!("{}", CONNS * REQ_PER_CONN);
    println!("{}", sum);
}
