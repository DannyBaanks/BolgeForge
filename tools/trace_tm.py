#!/usr/bin/env python3
import sys

XLAT1 = "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha"
XLAT2 = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
MEM_SIZE = 59049

def op(x, y):
    i = 0
    p9 = (1, 9, 81, 729, 6561)
    o = (
        (4, 3, 3, 1, 0, 0, 1, 0, 0),
        (4, 3, 5, 1, 0, 2, 1, 0, 2),
        (5, 5, 4, 2, 2, 1, 2, 2, 1),
        (4, 3, 3, 1, 0, 0, 7, 6, 6),
        (4, 3, 5, 1, 0, 2, 7, 6, 8),
        (5, 5, 4, 2, 2, 1, 8, 8, 7),
        (7, 6, 6, 7, 6, 6, 4, 3, 3),
        (7, 6, 8, 7, 6, 8, 4, 3, 5),
        (8, 8, 7, 8, 8, 7, 5, 5, 4),
    )
    for j in range(5):
        i += o[(y // p9[j]) % 9][(x // p9[j]) % 9] * p9[j]
    return i

def rot(x):
    return (x // 3) + (x % 3) * 19683

def trace_run(prog, in_char, max_steps=40):
    mem = list(prog) + [0] * (MEM_SIZE - len(prog))
    for i in range(len(prog), MEM_SIZE):
        mem[i] = op(mem[i - 1], mem[i - 2])

    a = c = d = 0
    step = 0
    print(f"--- TRACE FOR INPUT '{chr(in_char)}' (ASCII {in_char}) ---")
    while step < max_steps:
        raw = mem[c]
        if raw < 33 or raw > 126:
            instr = 'NOP'
        else:
            instr = XLAT1[(raw - 33 + c) % 94]
        
        print(f"step {step:2d}: c={c:3d} (mem[c]={raw:5d}), d={d:3d} (mem[d]={mem[d]:5d}), a={a:5d} | instr='{instr}'")
        
        if instr == 'j':
            d = mem[d]
        elif instr == 'i':
            c = mem[d]
        elif instr == '*':
            mem[d] = rot(mem[d])
            a = mem[d]
        elif instr == 'p':
            mem[d] = op(a, mem[d])
            a = mem[d]
        elif instr == '<':
            print(f"  OUTPUT: {a & 255} ('{chr(a & 255) if 32 <= (a & 255) <= 126 else '?'}')")
        elif instr == '/':
            a = in_char
        elif instr == 'v':
            print("  HALT!")
            return
        
        if 33 <= raw <= 126:
            mem[c] = ord(XLAT2[raw - 33])
            
        c = 0 if c == 59048 else c + 1
        d = 0 if d == 59048 else d + 1
        step += 1

if __name__ == "__main__":
    with open("artifacts/test_tm2.mal", "rb") as f:
        prog = list(f.read())
    trace_run(prog, ord('0'), 20)
    print()
    trace_run(prog, ord('1'), 20)
