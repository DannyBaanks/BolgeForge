import sys
XLAT1 = "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha"
XLAT2 = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
O = [[4,3,3,1,0,0,1,0,0],[4,3,5,1,0,2,1,0,2],[5,5,4,2,2,1,2,2,1],
     [4,3,3,1,0,0,7,6,6],[4,3,5,1,0,2,7,6,8],[5,5,4,2,2,1,8,8,7],
     [7,6,6,7,6,6,4,3,3],[7,6,8,7,6,8,4,3,5],[8,8,7,8,8,7,5,5,4]]
P9 = [1,9,81,729,6561]
def op(x,y):
    i = 0
    for j in range(5): i += O[(y//P9[j])%9][(x//P9[j])%9]*P9[j]
    return i
def rot(v): return v//3 + (v%3)*19683

def load(path):
    mem = [0]*59049
    i = 0
    with open(path,'rb') as f:
        for b in f.read():
            if chr(b).isspace(): continue
            assert 33 <= b <= 126, hex(b)
            mem[i] = b; i += 1
    while i < 59049:
        mem[i] = op(mem[i-1], mem[i-2]); i += 1
    return mem

def run(mem, until, log_from=None, log_to=None, instream=b""):
    a=c=d=0; ip=0; outp=bytearray(); step=0
    feed = list(instream); fi = 0
    while step < until:
        v = mem[c]
        if v < 33 or v > 126:
            c = 0 if c==59048 else c+1
            d = 0 if d==59048 else d+1
            step += 1
            continue
        instr = XLAT1[(v-33+c)%94]
        if log_from is not None and log_from <= step <= log_to:
            print(f"{step} c={c} d={d} {instr} a={a}" + (f" mem[c]={v}" if instr not in "jip*</ov" else ""))
        if instr == 'j': d = mem[d]
        elif instr == 'i': c = mem[d]
        elif instr == '*': a = mem[d] = rot(mem[d])
        elif instr == 'p': a = mem[d] = op(a, mem[d])
        elif instr == '<': outp.append(a & 255)
        elif instr == '/':
            if fi < len(feed): a = feed[fi]; fi += 1
            else: a = 59048
        elif instr == 'v':
            step += 1; break
        if 33 <= mem[c] <= 126: mem[c] = ord(XLAT2[mem[c]-33])
        c = 0 if c==59048 else c+1
        d = 0 if d==59048 else d+1
        step += 1
    return step, c, d, a, bytes(outp)

mem = load('artifacts/candidate_m281_53562b.mal')
step, c, d, a, out = run(mem, 25445)
print("after 25445 steps:", step, c, d, a)
print("expected from snapshot: 25445 25560 155 20173")
mem2 = load('artifacts/candidate_m281_53562b.mal')
print("---- replay window 25452..25469 ----")
run(mem2, 25470, log_from=25452, log_to=25469)
