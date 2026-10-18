#!/usr/bin/env python3
"""K2 branch-search diagnosis: where do the constraints die?"""
import pickle
from collections import Counter
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

def main():
    with open(Path(__file__).parent / "k2_reach_full.pkl", "rb") as f:
        data = pickle.load(f)
    depth = data["depth"]
    reach = sorted(depth.keys())

    d3c = Counter(digits(v)[3] for v in reach)
    print("reachable values by digit3:", dict(sorted(d3c.items())))
    d4_among_d3eq8 = Counter(digits(v)[4] for v in reach if digits(v)[3] == 8)
    print("digit4 distribution among digit3==8 reachables:", dict(sorted(d4_among_d3eq8.items())))

    yf8 = [v for v in reach if digits(v)[3] == 8]
    print(f"y_f candidates with digit3=8: {len(yf8)}, sample:", yf8[:10])

    # For gate (A,B): need digit4 of op(B,yf)==3 and op(A,yf)==3,
    # and digit3 op(B,yf)=O[8][B3]=8 -> B3 in {0,1,3,4}, same A.
    # Count gate pairs satisfying A3,B3 in {0,1,3,4}:
    viable = {}
    for j in (0, 1):
        viable[j] = {(k1, k2) for k1 in range(9) for k2 in range(9)
                     if len({O[k2][O[k1][v]] for v in range(9)}) == 1}
    viable[2] = {(k1, k2) for k1 in range(9) for k2 in range(9)
                 if len({O[k2][O[k1][v]] for v in range(4)}) == 1}
    from collections import defaultdict
    buckets = defaultdict(list)
    for v in reach:
        d = digits(v)
        buckets[(d[0], d[1], d[2])].append(v)
    ok_pairs = 0
    tot = 0
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
                        B3 = O[d2[3]][O[d1[3]][0]]
                        A3 = O[d2[3]][O[d1[3]][2]]
                        tot += 1
                        if A3 in (0, 1, 3, 4) and B3 in (0, 1, 3, 4):
                            ok_pairs += 1
    print(f"gate pairs: {tot}, with A3&B3 in mirror-8 set: {ok_pairs}")

    # Best structural probe: fix a few gate pairs and check op(B,yf) digit4/3 achievable
    print("\nSample feasibility for K1=19691 K2=29880 (A=8010 B=720):")
    for label, X in (("B", 720), ("A", 8010)):
        dx = digits(X)
        for y in yf8[:2000]:
            dy = digits(y)
            r = [O[dy[j]][dx[j]] for j in range(5)]
            if r[3] == 8 and r[4] == 3 and r[1] == 5 and r[2] == 6:
                print(f"  {label}: yf={y} -> {sum(t*p for t,p in zip(r,P9))}")

if __name__ == "__main__":
    main()
