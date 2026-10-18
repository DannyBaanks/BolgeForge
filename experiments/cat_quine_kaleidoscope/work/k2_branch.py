#!/usr/bin/env python3
"""K2: final branch-write search.

After gate, a = B (payload) or A (EOF). Final write: mem[d3] = op(a, y_f).
If routing returns d to d3, i lands at op(a, y_f) + 1. The routing is not
modeled here: p increments d, so a consecutive p;i does not read back d3.
Want:
  data:  echo entry  Et = op(B, y_f)+1  in free block [25647..25946]
  EOF:   halt cell   Ht = op(A, y_f)+1  also in free block (byte 'v' there), Ht != Et
y_f (the second write arg) must be a reachable value (from k2_reach_full.pkl).
Gate pairs enumerated per-digit as in k2_gate.py.
This variant restricts y_f digit3 to 8; use k2_branch2.py for the full sweep.
"""
import pickle
from collections import defaultdict
from pathlib import Path

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

def digits(v):
    return [(v // P9[j]) % 9 for j in range(5)]

def from_digits(ds):
    return sum(d * p for d, p in zip(ds, P9))

def opw(x, y):
    return sum(O[(y // P9[j]) % 9][(x // P9[j]) % 9] * P9[j] for j in range(5))

def main():
    with open(Path(__file__).parent / "k2_reach_full.pkl", "rb") as f:
        data = pickle.load(f)
    depth = data["depth"]
    reach = sorted(depth.keys())
    eof = digits(59048)

    viable = {}
    for j in (0, 1):
        viable[j] = {(k1, k2) for k1 in range(9) for k2 in range(9)
                     if len({O[k2][O[k1][v]] for v in range(9)}) == 1}
    viable[2] = {(k1, k2) for k1 in range(9) for k2 in range(9)
                 if len({O[k2][O[k1][v]] for v in range(4)}) == 1}

    # collect gate candidates with cheap total depth
    buckets = defaultdict(list)
    for v in reach:
        d = digits(v)
        buckets[(d[0], d[1], d[2])].append(v)
    gates = []
    for k1v in reach:
        d1 = digits(k1v)
        allowed0 = {k2 for (x, k2) in viable[0] if x == d1[0]}
        allowed1 = {k2 for (x, k2) in viable[1] if x == d1[1]}
        allowed2 = {k2 for (x, k2) in viable[2] if x == d1[2]}
        if not allowed0 or not allowed1 or not allowed2:
            continue
        for k20 in allowed0:
            for k21 in allowed1:
                for k22 in allowed2:
                    for k2v in buckets.get((k20, k21, k22), ()):
                        d2 = digits(k2v)
                        B = from_digits([O[d2[j]][O[d1[j]][0]] for j in range(5)])
                        A = from_digits([O[d2[j]][O[d1[j]][eof[j]]]
                                         for j in range(5)])
                        if A == B:
                            continue
                        cost = depth[k1v] + depth[k2v]
                        if cost <= 22:
                            gates.append((cost, k1v, k2v, A, B))
    gates.sort()
    print(f"gate candidates (cost<=22): {len(gates)}")

    # landing-1 cells: entry-1 must be a SAFE cell in the digit3=8 zone [25515..26243]
    safe_zone = (set(range(25647, 25947)) | set(range(25949, 25975)) |
                 set(range(25977, 26004)) | {26006, 26007} |
                 set(range(26010, 26098)) | {26100} | set(range(26103, 26123)) |
                 {26191, 26195})
    cand_block = {a - 1 for a in safe_zone}
    seen = set()
    hits = []
    yf8 = [v for v in reach if digits(v)[3] == 8]
    for cost, k1v, k2v, A, B in gates:
        key = (A, B)
        if key in seen:
            continue
        seen.add(key)
        for yf in yf8:
            td = opw(B, yf)
            te = opw(A, yf)
            if td in cand_block and te in cand_block and td != te:
                hits.append((cost + depth[yf], cost, k1v, k2v, A, B, yf, td, te))
    hits.sort()
    print(f"designs with BOTH landings in safe zone (yf digit3=8): {len(hits)}")
    for h in hits[:30]:
        tc, cost, k1v, k2v, A, B, yf, td, te = h
        print(f"  total~{tc} costs={cost}+{depth[yf]} K1={k1v} K2={k2v} "
              f"A={A} B={B} yf={yf}(d{depth[yf]}) echo_entry={td+1} halt_cell={te+1}")

if __name__ == "__main__":
    main()
