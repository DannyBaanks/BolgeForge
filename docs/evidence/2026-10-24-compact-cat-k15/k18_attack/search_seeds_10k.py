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
def run(seed):
    ops=synthesize_preamble_ops(CLEAN,HIGH,HD,9003,delta=94*18,template_clean=TEMPLATE,
        borrow_penalty=1,direct_gap=18,rng=random.Random(seed),restart_p1=0.80,restart_p2=0.90)
    return seed,len(ops)
if __name__=='__main__':
    with Pool(12) as pool:
        rows=pool.map(run,range(10000),chunksize=20)
    rows.sort(key=lambda r:r[1])
    print('k18 pen1 0.80/0.90 all121: min',rows[0][1],'seed',rows[0][0],'best10',rows[:10],'fits',sum(1 for _,n in rows if n<=7213))
