#!/usr/bin/env python3
"""K2: digit-wise 2-p gate search over REACHABLE constants.

Gate: F(x) = op(op(x, K1), K2). digit_j(F(x)) = O[K2_j][O[K1_j][digit_j(x)]].
Constant over ch in 0..255 <=> per-digit constancy over the digit ranges
that occur in [0..255]: digit0,digit1 span 0..8; digit2 spans 0..3; digit3,4 = 0.
EOF (59048) = all base-9 digits 8 (all ternary trits 2) -> A. Want A != B.
K1, K2 must be reachable values (depths from k2_reach_full.pkl).
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

def main():
    with open(Path(__file__).parent / "k2_reach_full.pkl", "rb") as f:
        data = pickle.load(f)
    depth = data["depth"]
    reach = sorted(depth.keys())
    eof = digits(59048)

    # viable[j] set of (k1,k2) pairs for digit position j
    viable = {}
    for j in (0, 1):
        viable[j] = {(k1, k2) for k1 in range(9) for k2 in range(9)
                     if len({O[k2][O[k1][v]] for v in range(9)}) == 1}
    viable[2] = {(k1, k2) for k1 in range(9) for k2 in range(9)
                 if len({O[k2][O[k1][v]] for v in range(4)}) == 1}
    print("viable pairs per position:",
          {j: len(viable[j]) for j in viable})

    # index reachable K2 by (d0,d1,d2); iterate K1
    buckets = defaultdict(list)
    for v in reach:
        d = digits(v)
        buckets[(d[0], d[1], d[2])].append(v)

    # precompute for each k1 the allowed k2 per position
    cand = 0
    best = []
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
                        # B: digit0 const value etc (use v=0..8 / 0..3)
                        B0 = O[d2[0]][O[d1[0]][0]]
                        B1 = O[d2[1]][O[d1[1]][0]]
                        B2 = O[d2[2]][O[d1[2]][0]]
                        # digit3,4: ch digit = 0 -> B3 = O[d2[3]][O[d1[3]][0]]
                        B3 = O[d2[3]][O[d1[3]][0]]
                        B4 = O[d2[4]][O[d1[4]][0]]
                        B = from_digits([B0, B1, B2, B3, B4])
                        A = from_digits([O[d2[j]][O[d1[j]][eof[j]]]
                                         for j in range(5)])
                        if A == B:
                            continue
                        cand += 1
                        cost = depth[k1v] + depth[k2v]
                        best.append((cost, k1v, k2v, A, B))
    best.sort()
    print(f"viable (K1,K2) reachable pairs: {cand}")
    for cost, k1v, k2v, A, B in best[:40]:
        print(f"  cost~{cost} K1={k1v}(d{depth[k1v]}) K2={k2v}(d{depth[k2v]}) A(EOF)={A} B(data)={B}")

if __name__ == "__main__":
    main()
