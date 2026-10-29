#!/usr/bin/env python3
"""Regenerate the matched, software-only i64 AES benchmark ports.

The reference kernels are transliterations of Xu's byte algorithm, NOT the
correctness oracle. Gold uses cryptography/OpenSSL; key schedules independently
use the FIPS 197 S-box and word expansion, checked against Appendix A.
The transliteration covers this kernel's limited syntax; every port must pass
the independent gold before performance results can be accepted.
Run from the repository root; generation needs the optional cryptography package.
"""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
from test_aes_conformance import Oracle, PT

N_BLOCKS = 100000
N_KEYS = 10000
SBOX = bytes.fromhex(
    '637c777bf26b6fc53001672bfed7ab76ca82c97dfa5947f0add4a2af9ca472c0'
    'b7fd9326363ff7cc34a5e5f171d8311504c723c31896059a071280e2eb27b275'
    '09832c1a1b6e5aa0523bd6b329e32f8453d100ed20fcb15b6acbbe394a4c58cf'
    'd0efaafb434d338545f9027f503c9fa851a3408f929d38f5bcb6da2110fff3d2'
    'cd0c13ec5f974417c4a77e3d645d197360814fdc222a908846eeb814de5e0bdb'
    'e0323a0a4906245cc2d3ac629195e479e7c8376d8dd54ea96c56f4ea657aae08'
    'ba78252e1ca6b4c6e8dd741f4bbd8b8a703eb5664803f60e613557b986c11d9e'
    'e1f8981169d98e949b1e87e9ce5528df8ca1890dbfe6426841992d0fb054bb16')
SCHEDULES = (
    ('2b7e151628aed2a6abf7158809cf4f3c','d014f9a8c9ee2589e13f0cc8b6630ca6'),
    ('8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b','e98ba06f448c773c8ecc720401002202'),
    ('603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4','fe4890d1e6188d0b046df344706c631e'),
)

def schedule(key):
    words = [list(key[i:i+4]) for i in range(0,len(key),4)]
    nk = len(words)
    rc = 1
    for i in range(nk,4*(nk+7)):
        t = words[-1][:]
        if i % nk == 0:
            t = [SBOX[b] for b in t[1:]+t[:1]]
            t[0] ^= rc
            rc = (rc << 1) ^ (0x11b if rc & 128 else 0)
        elif nk == 8 and i % nk == 4:
            t = [SBOX[b] for b in t]
        words.append([a ^ b for a,b in zip(words[i-nk],t)])
    return bytes(b for word in words for b in word)


def indices(text, lang):
    # Convert every Rust slice index recursively; keep array-valued byte indices
    # separate from their native index type. C's Vec carries data/len/cap.
    result = ''
    i = 0
    while i < len(text):
        m = re.match(r'(c\.(?:rk|sbox|inv)|sbox|s|w|key|src)\[',text[i:])
        if not m:
            result += text[i]; i += 1; continue
        start = i + len(m[0]); end = start; depth = 1
        while depth:
            if text[end] == '[': depth += 1
            if text[end] == ']': depth -= 1
            end += 1
        inner = indices(text[start:end-1],lang)
        name = m[1]
        result += (name + '.data[' + inner + ']' if lang == 'c' else name + '[(' + inner + ') as usize]')
        i = end
    return result


def translate(body, lang):
    result = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith('//'): continue
        line = line.replace('[]int{}', 'EMPTY')
        line = line.replace('string_from_bytes(s)', 's')
        line = line.replace('$&s', {'c':'s','go':'s','rs':'&mut s','swift':'&s'}[lang])
        for var in ('key','src'):
            line = line.replace(var + '.len', {'c':var+'.len','go':'int64(len('+var+'))','rs':var+'.len() as i64','swift':var+'.count'}[lang])
        m = re.fullmatch(r'for (\w+) in 0:(.+) \{',line)
        if m:
            var, bound = m.groups()
            line = {'c':f'for (int64_t {var}=0; {var} < {bound}; {var}++) {{',
                    'go':f'for {var} := int64(0); {var} < {bound}; {var}++ {{',
                    'rs':f'for {var} in 0i64..({bound}) {{',
                    'swift':f'for {var} in 0..<({bound}) {{'}[lang]
        else:
            m = re.fullmatch(r'(\$)?(\w+) := (.+)',line)
            if m:
                mut, var, expr = m.groups()
                array = expr == 'EMPTY' or expr.startswith('load16(')
                boolean = expr in ('true','false')
                if expr == 'EMPTY':
                    expr = {'c':'vnew()','go':'[]int64{}','rs':'Vec::<i64>::new()','swift':'[Int]()'}[lang]
                if lang == 'c': line = ('Vec' if array else 'bool' if boolean else 'int64_t') + ' ' + var + ' = ' + expr
                if lang == 'go': line = var + ' := ' + (expr if array or boolean else 'int64('+expr+')')
                if lang == 'rs': line = 'let ' + ('mut ' if mut else '') + var + ('' if array else ': bool' if boolean else ': i64') + ' = ' + expr
                if lang == 'swift': line = ('var ' if mut else 'let ') + var + ' = ' + expr
            else:
                m = re.fullmatch(r'(\w+)\.push\((.+)\)',line)
                if m:
                    var, expr = m.groups()
                    line = {'c':f'vpush(&{var}, {expr})','go':f'{var} = append({var}, {expr})',
                            'rs':f'{var}.push({expr})','swift':f'{var}.append({expr})'}[lang]
                elif line.startswith('<< '):
                    line = 'return ' + line[3:]
                    if lang == 'c' and line == 'return s': line = 'return s'
                elif line.startswith('while ') and lang == 'go': line = 'for ' + line[6:]
        line = line.replace('EMPTY', {'c':'vnew()', 'go':'[]int64{}', 'rs':'Vec::<i64>::new()', 'swift':'[Int]()'}[lang])
        # Rust needs borrowed parameter signatures, C passes Vec views.
        if lang in ('c','rs'): line = indices(line,lang)
        if lang in ('c','rs') and not line.endswith(('{','}')): line += ';'
        if lang == 'c' and line.startswith(('if ','while ')):
            at = line.rfind(' {'); head,cond = line.split(' ',1)
            line = head+' ('+cond[:at-len(head)-1]+') {'
        result.append(line)
    return '\n'.join(result)


def main():
    original = (ROOT/'src/crypto/aes/mod.xu').read_text()
    def body(name):
        start = re.search(r'(?:pub )?fn (?:\(c &Cipher\) )?'+name+r'\([^\n]*\) [^\n]*\{',original).end()
        depth=1; end=start
        while depth:
            if original[end]=='{': depth+=1
            if original[end]=='}': depth-=1
            end+=1
        code=original[start:end-1]
        # remove both invalid-block guard statements together
        code=re.sub(r'\n    if src.len != 16 \{\n        >> errors.new\([^\n]+\n    \}', '', code)
        return code
    names = ['xtime','rotl8','make_sbox','rcon','expand_key','shift_rows','inv_shift_rows','load16','encrypt','decrypt']
    csign = ['int64_t xtime(int64_t a)','int64_t rotl8(int64_t x,int64_t n)','Vec make_sbox(void)',
             'int64_t rcon(int64_t n)','Vec expand_key(Vec key,Vec sbox)','void shift_rows(Vec s)',
             'void inv_shift_rows(Vec s)','Vec load16(Vec src)','Vec encrypt(Cipher c,Vec src)','Vec decrypt(Cipher c,Vec src)']
    rsign = ['fn xtime(a:i64)->i64','fn rotl8(x:i64,n:i64)->i64','fn make_sbox()->Vec<i64>',
             'fn rcon(n:i64)->i64','fn expand_key(key:&[i64],sbox:&[i64])->Vec<i64>','fn shift_rows(s:&mut [i64])',
             'fn inv_shift_rows(s:&mut [i64])','fn load16(src:&[i64])->Vec<i64>','fn encrypt(c:&Cipher,src:&[i64])->Vec<i64>','fn decrypt(c:&Cipher,src:&[i64])->Vec<i64>']
    gsign = ['func xtime(a int64) int64','func rotl8(x,n int64) int64','func make_sbox() []int64',
             'func rcon(n int64) int64','func expand_key(key,sbox []int64) []int64','func shift_rows(s []int64)',
             'func inv_shift_rows(s []int64)','func load16(src []int64) []int64','func encrypt(c Cipher,src []int64) []int64','func decrypt(c Cipher,src []int64) []int64']
    ssign = ['func xtime(_ a:Int)->Int','func rotl8(_ x:Int,_ n:Int)->Int','func make_sbox()->[Int]',
             'func rcon(_ n:Int)->Int','func expand_key(_ key:[Int],_ sbox:[Int])->[Int]','func shift_rows(_ s:inout [Int])',
             'func inv_shift_rows(_ s:inout [Int])','func load16(_ src:[Int])->[Int]','func encrypt(_ c:Cipher,_ src:[Int])->[Int]','func decrypt(_ c:Cipher,_ src:[Int])->[Int]']
    header='// Generated by generate_aes_benches.py; software byte algebra, NOT an independent oracle.\n// Xu algorithm SHA256: '+hashlib.sha256(original.encode()).hexdigest()+'\n'
    chead='''#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
typedef struct {int64_t *data; int64_t len,cap;} Vec;
typedef struct {int64_t nr; Vec rk,sbox,inv;} Cipher;
static Vec vnew(void) { return (Vec){0}; }
static void vpush(Vec *v,int64_t x) { if(v->len==v->cap) {v->cap=v->cap?v->cap*2:4; v->data=realloc(v->data,v->cap*sizeof(int64_t)); if(!v->data) exit(1);} v->data[v->len++]=x; }
static void vfree(Vec v) {free(v.data);}
'''
    heads={'c':chead,'rs':'struct Cipher {nr:i64,rk:Vec<i64>,sbox:Vec<i64>,inv:Vec<i64>}\n',
           'go':'package main\nimport "fmt"\ntype Cipher struct {nr int64; rk,sbox,inv []int64}\n',
           'swift':'struct Cipher {let nr:Int;let rk:[Int];let sbox:[Int];let inv:[Int]}\n'}
    ctails='''static Cipher new_cipher(Vec key) {
    Vec sbox=make_sbox(),inv=vnew();
    for(int64_t i=0;i<256;i++) vpush(&inv,0);
    for(int64_t i=0;i<256;i++) inv.data[sbox.data[i]]=i;
    return (Cipher){key.len/4+6,expand_key(key,sbox),sbox,inv};
}
static void cfree(Cipher c) {vfree(c.rk);vfree(c.sbox);vfree(c.inv);}
static void aes_bench(int64_t bits,int64_t op) {
    Vec key=vnew(),block=vnew();
    for(int64_t i=0;i<bits/8;i++) vpush(&key,i);
    for(int64_t i=0;i<16;i++) vpush(&block,i*17);
    if(op==2) {int64_t sum=0; for(int64_t i=0;i<10000;i++) {key.data[0]=i&255; Cipher c=new_cipher(key);sum+=c.rk.data[c.rk.len-16+(i&15)];cfree(c);} printf("%lld\\n",(long long)sum);}
    else {Cipher c=new_cipher(key);for(int64_t i=0;i<100000;i++) {Vec next=op==0?encrypt(c,block):decrypt(c,block);vfree(block);block=next;}for(int64_t i=0;i<16;i++) printf("%02x",(unsigned)block.data[i]);puts("");cfree(c);}
    vfree(key);vfree(block);
}
'''
    rtails='''fn new_cipher(key:&[i64])->Cipher {
    let sbox=make_sbox(); let mut inv=vec![0i64;256];
    for i in 0..256 {inv[sbox[i] as usize]=i as i64;}
    let rk=expand_key(key,&sbox); Cipher{nr:key.len() as i64/4+6,rk,sbox,inv}
}
pub fn aes_bench(bits:i64,op:i64) {
    let mut key:Vec<i64>=(0..bits/8).collect();let mut block:Vec<i64>=(0..16).map(|i|i*17).collect();
    if op==2 {let mut sum=0i64;for i in 0..10000 {key[0]=i&255;let c=new_cipher(&key);sum+=c.rk[c.rk.len()-16+(i as usize&15)];}println!("{}",sum);}
    else {let c=new_cipher(&key);for _ in 0..100000 {block=if op==0 {encrypt(&c,&block)} else {decrypt(&c,&block)};}for b in block {print!("{:02x}",b);}println!();}
}
'''
    gtails='''func new_cipher(key []int64) Cipher {
    sbox:=make_sbox();inv:=make([]int64,256);for i:=int64(0);i<256;i++ {inv[sbox[i]]=i};return Cipher{int64(len(key))/4+6,expand_key(key,sbox),sbox,inv}
}
func aes_bench(bits,op int64) {
    key:=make([]int64,bits/8);block:=make([]int64,16);for i:=int64(0);i<bits/8;i++ {key[i]=i};for i:=int64(0);i<16;i++ {block[i]=i*17}
    if op==2 {sum:=int64(0);for i:=int64(0);i<10000;i++ {key[0]=i&255;c:=new_cipher(key);sum+=c.rk[len(c.rk)-16+int(i&15)]};fmt.Println(sum)}
    else {c:=new_cipher(key);for i:=int64(0);i<100000;i++ {if op==0 {block=encrypt(c,block)} else {block=decrypt(c,block)}};for _,b:=range block {fmt.Printf("%02x",b)};fmt.Println()}
}
'''
    stails='''func new_cipher(_ key:[Int])->Cipher {
    let sbox=make_sbox();var inv=[Int](repeating:0,count:256);for i in 0..<256 {inv[sbox[i]]=i};return Cipher(nr:key.count/4+6,rk:expand_key(key,sbox),sbox:sbox,inv:inv)
}
func aes_bench(_ bits:Int,_ op:Int) {
    var key=Array(0..<bits/8);var block=(0..<16).map{$0*17}
    if op==2 {var sum=0;for i in 0..<10000 {key[0]=i&255;let c=new_cipher(key);sum+=c.rk[c.rk.count-16+(i&15)]};print(sum)}
    else {let c=new_cipher(key);for _ in 0..<100000 {block=op==0 ? encrypt(c,block) : decrypt(c,block)};let h=Array("0123456789abcdef".utf8);var out=[UInt8]();for b in block {out.append(h[b>>4]);out.append(h[b&15])};print(String(decoding:out,as:UTF8.self))}
}
'''
    cross=ROOT/'tests/bench/cross'
    for lang,signs,tail in [('c',csign,ctails),('rs',rsign,rtails),('go',gsign,gtails),('swift',ssign,stails)]:
        text=header+heads[lang]
        for name,sign in zip(names,signs): text+=('static ' if lang=='c' else '')+sign+' {\n'+translate(body(name),lang)+'\n}\n'
        text+=tail
        # Go requires else to share the closing-brace line.
        if lang=='go': text=re.sub(r'}\s*\n\s*else', '} else', text)
        (cross/('aes_software.'+('h' if lang=='c' else lang))).write_text(text)
    oracle=Oracle()
    if not oracle.Cipher: raise RuntimeError('generation needs cryptography (the checked-in benchmarks do not)')
    for key,last in SCHEDULES: assert schedule(bytes.fromhex(key))[-16:].hex()==last
    rows=[]
    for bits in (128,192,256):
        key=bytes(range(bits//8))
        for op,tag in enumerate(('encrypt','decrypt','key_setup')):
            name=f'aes{bits}_{tag}'
            if op==2:
                cache=[schedule(bytes([i])+key[1:])[-16:] for i in range(256)]
                expect=str(sum(cache[i&255][i&15] for i in range(N_KEYS)))+'\n'
                xu=f'''@main
#crypto/aes
fn main() int {{
    $key := make_string({bits//8})
    for j in 0:key.len {{key[j]=j}}
    $checksum:=0
    for i in 0:{N_KEYS} {{
        key[0]=i&255
        c:=aes.new_cipher(&key) or (err) {{<<1}}
        checksum=checksum+c.rk[c.rk.len-16+(i&15)]
    }}
    println(checksum)
    <<0
}}
'''
            else:
                cipher=oracle.Cipher(oracle.algorithms.AES(key),oracle.modes.ECB())
                ctx=cipher.encryptor() if op==0 else cipher.decryptor()
                block=PT
                for _ in range(N_BLOCKS): block=ctx.update(block)
                assert ctx.finalize()==b''
                expect=block.hex()+'\n'
                xu=f'''@main
#crypto/aes
#encoding/hex
fn main() int {{
    key:=hex.decode_string("{key.hex()}") or (err) {{<<1}}
    c:=aes.new_cipher(&key) or (err) {{<<1}}
    $block:=hex.decode_string("{PT.hex()}") or (err) {{<<1}}
    for i in 0:{N_BLOCKS} {{block=c.{tag}(&block) or (err) {{<<1}}}}
    println(hex.encode_to_string(block))
    <<0
}}
'''
            (ROOT/'tests/bench'/f'{name}.xu').write_text(xu)
            (cross/f'{name}.c').write_text('#include "aes_software.h"\nint main(void) { aes_bench('+str(bits)+','+str(op)+');return 0;}\n')
            (cross/f'{name}.rs').write_text('mod aes_software;\nfn main() {aes_software::aes_bench('+str(bits)+','+str(op)+');}\n')
            (cross/f'{name}.go').write_text('package main\nfunc main() {aes_bench('+str(bits)+','+str(op)+')}\n')
            (cross/f'{name}.swift').write_text('@main struct Driver {static func main() {aes_bench('+str(bits)+','+str(op)+')}}\n')
            rows.append(dict(name=name,bits=bits,operation=tag,iterations=N_KEYS if op==2 else N_BLOCKS,expect=expect))
    (ROOT/'tests/bench/aes_cases.json').write_text(json.dumps(dict(oracle=oracle.identity,
        standard='https://csrc.nist.gov/pubs/fips/197/final',key_schedule_vectors=SCHEDULES,
        algorithm_sha256=hashlib.sha256(original.encode()).hexdigest(),rows=rows),indent=2)+'\n')
    print('\n'.join('    Bench('+repr(row['name'])+', '+repr(row['expect'])+', '+repr('AES软件 '+str(row['bits'])+' '+row['operation'])+', CORE, xu_opt_matrix=True),' for row in rows))

if __name__=='__main__': main()
