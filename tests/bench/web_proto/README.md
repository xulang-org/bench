# Web Backend, Network Protocols & Serialization Suite (Batch D)

Self-contained deterministic benchmarks covering real-world web frameworks, protocol codecs, configuration lexing, server-side HTML templating, and key-derivation / token signing hot paths. All 6 workloads provide five-language ports (`Xu`, `Go`, `C`, `Rust`, `Swift`) with LF-normalized deterministic stdout goldens.

| Benchmark | Domain / Algorithm | Scale | Golden |
|---|---|---|---|
| `http_router_parse` | Raw HTTP/1.1 request line + case-insensitive header parsing, trie dynamic routing (`:param`, `*`), `%XX`/`+` query decoding | 240 requests × 500 rounds | `106000\n493970096\n` |
| `websocket_frame` | RFC 6455 WebSocket wire framing (`7-bit`/`16-bit` lengths) encode + decode & 32-bit mask XOR | 80 frames × 180 rounds | `16882560\n995067448\n` |
| `protobuf_varint` | Protobuf v3 LEB128 varint, ZigZag `sint64`, packed repeated fields, nested sub-message batches | 400 batches × 500 msgs | `8738912\n198544933\n` |
| `toml_config_parse` | Multi-section TOML config lexer/parser (tables, `#` comments, escapes, bools, `_` ints, flat arrays) | 48 sections × 1000 rounds | `336000\n82034545\n` |
| `template_render` | HTML template opcode compiler + VM renderer (`{{var}}`, `{{{raw}}}`, `{%for%}`, `{%if%/%else%}`, XSS escaping) | 400 compiles × 25 pages | `11585000\n816359811\n` |
| `hmac_pbkdf2` | FIPS 180-4 SHA-256 + RFC 2104 HMAC-SHA256 + RFC 2898 PBKDF2-HMAC-SHA256 (`c=1000`, `dkLen=32`) | 80 KDF + 200 HMAC | `280\nf88ff7eadf3c76f6a2d3098ac8740bffb1fc75bf364f984233c86d1659bed2ec\n` |
