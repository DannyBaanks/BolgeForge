#!/usr/bin/env python3
"""K2 groundwork (2026-10-18): runtime-order EOF detector scan + target feasibility.

Verified semantics: oracle/mb_ref.c:77 -> p: a = mem[d] = op(a, mem[d]) (a first).
Question: which (K1,K2) pairs give a collision-free EOF gate under RUNTIME order?
Also: search loadable small constants (33..126), pad-chain luck, and branch-write ranges.
"""
from pathlib import Path

ART = Path("artifacts/candidate_m281_53562b.mal")
MEM_SIZE = 59049

P9 = [1, 9, 81, 729, 6561]
O = [
    [4, 3, 3, 1, 0, 0, 1, 0, 0],
    [4, 3, 5, 1, 0, 2, 1, 0, 2],
    [5, 5, 4, 2, 2, 1, 2, 2, 1],
    [4, 3, 3, 1, 0, 0, 7, 6, 6],
    [4, 3, 5, 1, 0, 2, 7, 6, 8],
    [5, 5, 4, 2, 2, 1, 8, 8, 7],
    [7, 6, 6, 7, 6, 6, 4, 3, 3],
    [7, 6, 8, 7, 6, 8, 4, 3, 5],
    [8, 8, 7, 8, 8, 7, 5, 5, 4],
]

def crazy(x, y):
    i = 0
    for j in range(5):
        i += O[(y // P9[j]) % 9][(x // P9[j]) % 9] * P9[j]
    return i

def rot(x):
    return (x // 3) + (x % 3) * 19683

def main():
    payload = list(range(256))
    print("== A. Published detectors, BOTH orders (runtime = a first) ==")
    for (k1, k2, name) in [(59048, 29524, "inv1"), (59048, 729, "inv3"), (59048, 162, "inv4")]:
        fwd = {ch: crazy(crazy(ch, k1), k2) for ch in payload}       # runtime order
        rev = {ch: crazy(crazy(k1, ch), k2) for ch in payload}       # doc order
        eof_fwd, eof_rev = crazy(crazy(59048, k1), k2), crazy(crazy(k1, 59048), k2)
        zf = sum(1 for v in fwd.values() if v == 0)
        zr = sum(1 for v in rev.values() if v == 0)
        cf = len(set(fwd.values())); cr = len(set(rev.values()))
        print(f"{name} ({k1},{k2}): RUNTIME eof={eof_fwd} zeros_on_256={zf} distinct={cf} "
              f"| doc-order eof={eof_rev} zeros={zr} distinct={cr}")
        if cf == 1:
            print(f"   runtime CONSTANT = {next(iter(fwd.values()))}")

    print("\n== B. Full scan (K1,K2) in 33..126, runtime order ==")
    const_hits, gate_hits = [], []
    for k1 in range(33, 127):
        f1 = {ch: crazy(ch, k1) for ch in payload}
        e1 = crazy(59048, k1)
        for k2 in range(33, 127):
            vals = set()
            for ch in payload:
                vals.add(crazy(f1[ch], k2))
                if len(vals) > 1:
                    break
            if len(vals) == 1:
                c = next(iter(vals))
                if crazy(e1, k2) != c:
                    const_hits.append((k1, k2, c, crazy(e1, k2)))
            eofv = crazy(e1, k2)
            if eofv == 0 and all(crazy(f1[ch], k2) != 0 for ch in payload):
                gate_hits.append((k1, k2))
    print(f"constant-detector pairs (non-EOF const != EOF out): {len(const_hits)}")
    for h in const_hits[:20]:
        print("   K1=%d K2=%d data_const=%d eof_out=%d" % h)
    print(f"collision-free gates with EOF->0: {len(gate_hits)}")
    for h in gate_hits[:20]:
        print("   K1=%d K2=%d" % h)

    print("\n== C. Pad chain of candidate_m281_53562b ==")
    raw = ART.read_bytes()
    clean = [b for b in raw if 33 <= b <= 126]
    mem = list(clean) + [0] * (MEM_SIZE - len(clean))
    for i in range(len(clean), MEM_SIZE):
        mem[i] = crazy(mem[i - 1], mem[i - 2])
    interesting = {59048: [], 729: [], 29524: [], 1458: [], 0: []}
    for addr in range(52829, MEM_SIZE):
        v = mem[addr]
        if v in interesting:
            interesting[v].append(addr)
    for v, addrs in interesting.items():
        print(f"   value {v}: {len(addrs)} pad cells", addrs[:5])
    inblock = [(a, mem[a]) for a in range(52829, MEM_SIZE) if 25647 <= mem[a] <= 25946]
    print(f"   pad values landing in free block [25647..25946]: {len(inblock)}", inblock[:5])
    lo = [(a, mem[a]) for a in range(52829, MEM_SIZE) if mem[a] <= 126]
    print(f"   pad values <=126 (usable as 2nd-arg seeds): {len(lo)}", lo[:10])

    print("\n== D. Branch-write feasibility for gate (59048,729): a in {0,1458} ==")
    r0 = sorted({crazy(0, y) for y in range(33, 127)})
    r1 = sorted({crazy(1458, y) for y in range(33, 127)})
    print(f"   op(0,y) range over y=33..126: [{r0[0]}..{r0[-1]}] n={len(r0)}")
    print(f"   op(1458,y) range: [{r1[0]}..{r1[-1]}] n={len(r1)}")
    windows = {
        "free_block": (25647, 25946),
        "lowblock": (3, 44),
        "pocket2": (25949, 25974),
        "pocket3": (25977, 26003),
    }
    best = []
    for y in range(33, 127):
        te, td = crazy(0, y), crazy(1458, y)
        for wname, (a0, a1) in windows.items():
            if a0 <= te <= a1 or a0 <= td <= a1:
                best.append((y, te, td, wname))
    print(f"   y with a target in a code window: {len(best)}")
    for b in best[:30]:
        print("   y=%d T_eof=%d T_data=%d window=%s" % b)

if __name__ == "__main__":
    main()
