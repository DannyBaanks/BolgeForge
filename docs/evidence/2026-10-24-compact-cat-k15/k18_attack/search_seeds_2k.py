import sys, random
from pathlib import Path
from multiprocessing import Pool
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(HERE))
from search_synth import extract_target_state, synthesize_preamble_ops
REF=ROOT/'reference'/'malbolge_org'/'cat.mal'
CLEAN,HIGH,HD,_=extract_target_state(REF,9003)
TEMPLATE=[b for b in REF.read_bytes() if 33<=b<=126]
VARIANTS=[]
for k in (16,17,18):
    for pen in (1,2):
        VARIANTS.append((k,pen,0.80,0.90))
def budget(k): return 8904-94*k
def run(job):
    v,seed=job; k,pen,p1,p2=v
    ops=synthesize_preamble_ops(CLEAN,HIGH,HD,9003,delta=94*k,template_clean=TEMPLATE,
        borrow_penalty=pen,direct_gap=18,rng=random.Random(seed),restart_p1=p1,restart_p2=p2)
    return v,seed,len(ops)
if __name__=='__main__':
    N=2000
    jobs=[(v,s) for v in VARIANTS for s in range(N)]
    with Pool(12) as pool:
        rows=pool.map(run,jobs,chunksize=10)
    for v in VARIANTS:
        sub=sorted((r for r in rows if r[0]==v),key=lambda r:r[2])
        b=budget(v[0])
        print(v,'budget',b,'min',sub[0][2],'seed',sub[0][1],'best5',[(r[1],r[2]) for r in sub[:5]],'fits',sum(1 for r in sub if r[2]<=b))
