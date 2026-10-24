import sys
sys.path.insert(0, ".")
import kernel_search as ks
from collections import Counter
from itertools import product
from multiprocessing import Pool

def sim_relaxed(prefix, max_steps=3000):
    mem = ks.build_state(prefix)
    a = c = d = 0
    out_n = 0
    for step in range(max_steps):
        if c >= ks.WINDOW or d >= ks.WINDOW:
            return ("ESCAPE", step, out_n)
        v = mem[c]
        if not (33 <= v <= 126):
            return ("NONPRINTABLE_PC", step, out_n)
        instr = ks.XLAT1[(v - 33 + c) % 94]
        if instr == "j": d = mem[d]
        elif instr == "i": c = mem[d]
        elif instr == "*": a = mem[d] = mem[d] // 3 + mem[d] % 3 * 19683
        elif instr == "p": a = mem[d] = ks.crazy(a, mem[d])
        elif instr == "<":
            out_n += 1
            if (a & 255) != 49:
                return ("WRONG_OUT", step, out_n)
        elif instr == "/":
            a = 59048
        elif instr == "v":
            return ("HALT", step, out_n)
        if c >= ks.WINDOW:
            return ("ESCAPE", step, out_n)
        v2 = mem[c]
        if not (33 <= v2 <= 126):
            return ("INVALID_ENCRYPTION", step, out_n)
        mem[c] = ord(ks.XLAT2[v2 - 33])
        c = (c + 1) % ks.MEM_SIZE
        d = (d + 1) % ks.MEM_SIZE
    return ("MAX_STEPS", step, out_n)

def job(prefix):
    return prefix, sim_relaxed(prefix)

if __name__ == "__main__":
    depth = int(sys.argv[1])
    cands = list(product(ks.OPS, repeat=depth))
    stats = Counter()
    surv = []
    with Pool(12) as pool:
        for prefix, res in pool.imap_unordered(job, cands, chunksize=64):
            stats[res[0]] += 1
            if res[0] == "MAX_STEPS":
                surv.append((prefix, res))
    print(f"profundidad {depth}: {len(cands)} programas; stats {dict(stats)}")
    surv.sort(key=lambda t: -t[1][2])
    for p, r in surv[:12]:
        print("".join(p), r)
