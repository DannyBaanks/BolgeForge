#!/usr/bin/env python3
"""K2 branch-search ladder: locate the constraint that kills both-landing designs."""
import pickle
from collections import defaultdict, Counter
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

SAFE_ZONE = (set(range(25647, 25947)) | set(range(25949, 25975)) |
             set(range(25977, 26004)) | {26006, 26007} |
             set(range(26010, 26098)) | {26100} | set(range(26103, 26123)) |
             {26191, 26195})
CAND = {a - 1 for a in SAFE_ZONE}

def main():
    with open(Path(__file__).parent / "k2_reach_full.pkl", "rb") as f:
        depth = pickle.load(f)["depth"]
    reach = sorted(depth.keys())

    viable = {}
    for j in (0, 1):
        viable[j] = {(k1, k2) for k1 in range(9) for k2 in range(9)
                     if len({O[k2][O[k1][v]] for v in range(9)}) == 1}
    viable[2] = {(k1, k2) for k1 in range(9) for k2 in range(9)
                 if len({O[k2][O[k1][v]] for v in range(4)}) == 1}
    buckets = defaultdict(list)
    for v in reach:
        d = digits(v)
        buckets[(d[0], d[1], d[2])].append(v)
    gates = []
    for k1v in reach:
        d1 = digits(k1v)
        a0 = {k2 for (x, k2) in viable[0] if x == d1[0]}
        a1 = {k2 for (x, k2) in viable[1] if x == d1[1]}
        a2 = {k2 for (x, k2) in viable[2] if x == d1[2]}
        if not a0 or not a1 or not a2:
            continue
        for k20 in a0:
            for k21 in a1:
                for k22 in a2:
                    for k2v in buckets.get((k20, k21, k22), ()):
                        d2 = digits(k2v)
                        B = from_digits([O[d2[j]][O[d1[j]][0]] for j in range(5)])
                        A = from_digits([O[d2[j]][O[d1[j]][2]] for j in range(5)])
                        if A != B:
                            gates.append((depth[k1v] + depth[k2v], k1v, k2v, A, B))
    gates.sort()
    print(f"gates total: {len(gates)}")

    yf_all = reach
    yf8 = [v for v in reach if digits(v)[3] == 8]
    print(f"yf lists: all={len(yf_all)} digit3=8={len(yf8)}")

    rng = set(range(25514, 26243))
    ladder = Counter()
    sample = []
    seen = set()
    for cost, k1v, k2v, A, B in gates:
        if (A, B) in seen:
            continue
        seen.add((A, B))
        for yf in yf8:
            te = opw(A, yf)
            td = opw(B, yf)
            if te in rng:
                ladder["te in zone-range"] += 1
            if td in rng:
                ladder["td in zone-range"] += 1
            if te in rng and td in rng:
                ladder["both in zone-range"] += 1
                if te in CAND and td in CAND:
                    ladder["both exact"] += 1
                    if len(sample) < 20:
                        sample.append((cost, k1v, k2v, A, B, yf, te, td))
            if ladder["both in zone-range"] > 5_000_000:
                break
        if ladder["both in zone-range"] > 5_000_000:
            break
    print("ladder:", dict(ladder))
    for s in sample:
        print("  ", s)

if __name__ == "__main__":
    main()
