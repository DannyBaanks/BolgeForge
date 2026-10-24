import sys, random
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(HERE))
import search_synth as R
from tools.verify_handoff_state import load_program, run_to_cell
from tools.test_compressed import verify_target, run, REFERENCE
from constants import XLAT1, XLAT2, MEM_SIZE, crazy_op, rot_op

REF=ROOT/'reference'/'malbolge_org'/'cat.mal'
OUT=Path('/tmp/opencode/cat_7690.mal')
LIN_END=9003; K=18; DELTA=94*K
DEAD2={58844,59046}
CLEAN,HIGH,HD,_=R.extract_target_state(REF,LIN_END)
TEMPLATE=[b for b in REF.read_bytes() if 33<=b<=126]
HIGH={a:v for a,v in HIGH.items() if a not in DEAD2}
ops=R.synthesize_preamble_ops(CLEAN,HIGH,HD,LIN_END,delta=DELTA,template_clean=TEMPLATE,
    borrow_penalty=2,direct_gap=18,rng=random.Random(1435),restart_p1=0.80,restart_p2=0.90)
print('preamble ops',len(ops))
raw,end_c=R.assemble_shifted_program(TEMPLATE,ops,CLEAN,LIN_END,DELTA)
assert raw is not None, end_c
OUT.write_bytes(raw)
cells=[b for b in raw if 33<=b<=126]
print('cells',len(cells),'end_c',end_c,'handoff target',LIN_END-DELTA,'pad',LIN_END-DELTA-end_c)

# handoff
rc,rm=load_program(REF); rin=list(rm)
a_ref,c_ref,d_ref,s_ref,st_ref=run_to_cell(rm,9067)
cc,cm=load_program(OUT)
a_c,c_c,d_c,s_c,st_c=run_to_cell(cm,9067-DELTA)
print(f'handoff ref a={a_ref} d={d_ref} cell={c_ref} ({st_ref}) | cand a={a_c} d={d_c} cell={c_c} ({st_c})')
variables={a:rm[a] for a in range(len(rc),MEM_SIZE) if rm[a]!=rin[a]}
wrong=[]; exempt=set()
for addr,val in sorted(variables.items()):
    exp=val-DELTA if LIN_END<val<len(rc) else val
    got=cm[addr]
    if addr in DEAD2:
        exempt.add(addr)
        continue
    if got!=exp: wrong.append((addr,exp,got))
print(f'variables {len(variables)}; exempt {sorted(exempt)}; wrong {len(wrong)}; a_ok={a_ref==a_c}; d_ok={d_ref==d_c}; cell_ok={c_c==9067-DELTA}')
for w in wrong[:8]: print('  wrong',w)

# outputs
print('repo battery:',verify_target('cat',OUT),'cases')
rng=random.Random(2026)
ext=[('empty',b''),('one',b'\x00'),('all256',bytes(range(256))),('256x16',bytes(range(256))*16),
     ('zeros64k',bytes(65536)),('random64k',bytes(rng.randrange(256) for _ in range(65536))),
     ('text60k',(b'the quick brown fox jumps over the lazy dog\n'*1400)[:60000])]
for name,payload in ext:
    got=run(OUT,payload); want=run(REFERENCE/'cat.mal',payload)
    print(f'  {name:10s} {len(payload):6d} -> {"OK" if got==want else "MISMATCH"} ({len(got)} bytes)')

# candidate loop trace
def trace(mem0,a0,c0,d0,data,limit=200_000_000):
    mem=list(mem0); a,c,d=a0,c0,d0; pos=0; acc=set(); steps=0
    while steps<limit:
        acc.add(c)
        ch=XLAT1[(mem[c]-33+c)%94]
        if ch=='j': acc.add(d); d=mem[d]
        elif ch=='i': acc.add(d); c=mem[d]
        elif ch=='*': acc.add(d); a=mem[d]=rot_op(mem[d])
        elif ch=='p': acc.add(d); a=mem[d]=crazy_op(a,mem[d])
        elif ch=='/':
            if pos<len(data): a=data[pos]; pos+=1
            else: a=59048
        elif ch=='v': return acc,steps,'HALT'
        elif ch=='<': pass
        mem[c]=ord(XLAT2[mem[c]-33]); c=(c+1)%MEM_SIZE; d=(d+1)%MEM_SIZE; steps+=1
    return acc,steps,'LIMIT'
_,cm2=load_program(OUT)
a2,c2,d2,_,_=run_to_cell(cm2,9067-DELTA)
acc,steps,status=trace(cm2,a2,c2,d2,bytes(rng.randrange(256) for _ in range(65536)))
print(f'candidate trace: {status} {steps} steps, {len(acc)} cells; exempt touched: {sorted(acc & DEAD2)}')
