package main

import (
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"strconv"
	"strings"
)

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

const conns = 16
const reqPerConn = 200

func expectedBody(seq int) string {
	return "pong-" + strconv.Itoa(seq) + "\n"
}

func fnvUpdate(h uint32, body string) uint32 {
	for i := 0; i < len(body); i++ {
		h ^= uint32(body[i])
		h *= 16777619
	}
	return h
}

func handler(w http.ResponseWriter, r *http.Request) {
	seq := strings.TrimPrefix(r.URL.Path, "/r/")
	w.Header().Set("Content-Type", "text/plain")
	fmt.Fprintf(w, "pong-%s\n", seq)
}

func worker(addr string, base int, out chan<- uint32) {
	h := uint32(2166136261)
	for i := 0; i < reqPerConn; i++ {
		seq := base + i
		conn, err := net.Dial("tcp", addr)
		if err != nil {
			fmt.Fprintln(os.Stderr, "dial:", err)
			os.Exit(1)
		}
		req := "GET /r/" + strconv.Itoa(seq) + " HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n"
		if _, err := conn.Write([]byte(req)); err != nil {
			fmt.Fprintln(os.Stderr, "write:", err)
			os.Exit(1)
		}
		resp, err := io.ReadAll(conn)
		conn.Close()
		if err != nil {
			fmt.Fprintln(os.Stderr, "read:", err)
			os.Exit(1)
		}
		raw := string(resp)
		idx := strings.Index(raw, "\r\n\r\n")
		if idx < 0 {
			fmt.Fprintln(os.Stderr, "no header end")
			os.Exit(1)
		}
		body := raw[idx+4:]
		if body != expectedBody(seq) {
			fmt.Fprintln(os.Stderr, "body mismatch")
			os.Exit(1)
		}
		h = fnvUpdate(h, body)
	}
	out <- h
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		fmt.Fprintln(os.Stderr, "listen:", err)
		os.Exit(1)
	}
	port := ln.Addr().(*net.TCPAddr).Port
	addr := "127.0.0.1:" + strconv.Itoa(port)
	srv := &http.Server{Handler: http.HandlerFunc(handler)}
	go srv.Serve(ln)

	out := make(chan uint32, conns)
	for w := 0; w < conns; w++ {
		go worker(addr, w*reqPerConn, out)
	}
	var sum uint64
	for i := 0; i < conns; i++ {
		sum += uint64(<-out)
	}
	fmt.Println(conns * reqPerConn)
	fmt.Println(sum)
}
