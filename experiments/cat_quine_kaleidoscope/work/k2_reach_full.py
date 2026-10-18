#!/usr/bin/env python3
"""K2: FULL reachability from a=19720 under {rot, p(y in 33..126)} - no depth cap.
Saves value -> (depth, parent, op) to work/k2_reach_full.pkl for later design use.
"""
import pickle
from collections import deque
from pathlib import Path

MEM = 59049
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
    return (O[(y // 1) % 9][(x // 1) % 9]
            + O[(y // 9) % 9][(x // 9) % 9] * 9
            + O[(y // 81) % 9][(x // 81) % 9] * 81
            + O[(y // 729) % 9][(x // 729) % 9] * 729
            + O[(y // 6561) % 9][(x // 6561) % 9] * 6561)

def rot(x):
    return (x // 3) + (x % 3) * 19683

def main():
    seeds = list(range(33, 127))
    START = 19720
    parent = {START: None}
    depth = {START: 0}
    q = deque([START])
    while q:
        u = q.popleft()
        du = depth[u]
        v = rot(u)
        if v not in parent:
            parent[v] = (u, "R")
            depth[v] = du + 1
            q.append(v)
        for y in seeds:
            v = crazy(u, y)
            if v not in parent:
                parent[v] = (u, ("P", y))
                depth[v] = du + 1
                q.append(v)
    print(f"FULL reachable: {len(parent)} / {MEM}")
    for t in (0, 81, 162, 729, 1458, 29524, 59046, 59047, 59048):
        print(f"  {t}: depth {depth.get(t, 'UNREACHABLE')}")
    mx = max(depth.values())
    print(f"max depth {mx}; values by depth>30: {sum(1 for d in depth.values() if d > 30)}")
    out = Path(__file__).parent / "k2_reach_full.pkl"
    with open(out, "wb") as f:
        pickle.dump({"depth": depth, "parent": parent}, f)
    print(f"saved {out}")

if __name__ == "__main__":
    main()
