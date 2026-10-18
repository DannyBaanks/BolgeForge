#!/usr/bin/env python3
"""K2: reachability of constants 59048 / 729 / others from C-entry a=19720.

Ops modeled: rot (execute *), p (execute p with 2nd arg y).
Phase 1: strict seeds y in [33..126] (values directly loadable in cells).
Phase 2: fixpoint -- any discovered value may be stored and reused as 2nd arg.
Reachability only; costs/cell layout to be designed after.
"""
from collections import deque

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
    i = 0
    for j in range(5):
        i += O[(y // P9[j]) % 9][(x // P9[j]) % 9] * P9[j]
    return i

def rot(x):
    return (x // 3) + (x % 3) * 19683

SEEDS = list(range(33, 127))
START = 19720
TARGETS = {59048: "C59048", 729: "C729", 29524: "C29524", 1458: "C1458",
           0: "ZERO", 162: "C162", 81: "C81"}

def bfs(available, label, max_depth=24):
    dist = {START: 0}
    parent = {START: None}
    q = deque([START])
    while q:
        u = q.popleft()
        d = dist[u]
        if d >= max_depth:
            continue
        for v, act in ((rot(u), "*"),) + tuple((crazy(u, y), ("p", y)) for y in available):
            if v not in dist:
                dist[v] = d + 1
                parent[v] = (u, act)
                q.append(v)
    print(f"== {label}: reachable {len(dist)} values within depth {max_depth} ==")
    for t, name in sorted(TARGETS.items()):
        if t in dist:
            path = []
            cur = t
            while parent[cur] is not None:
                u, act = parent[cur]
                path.append(act)
                cur = u
            path.reverse()
            print(f"  {name} = {t}: DEPTH {dist[t]}  path: {path}")
        else:
            print(f"  {name} = {t}: unreachable")
    return dist, parent

def main():
    print("orbit of 19720 under rot:", end=" ")
    v = START; orbit = []
    for _ in range(12):
        orbit.append(v); v = rot(v)
    print(orbit)

    dist1, _ = bfs(SEEDS, "Phase 1 strict seeds y in [33..126]")
    print(f"R1 size: {len(dist1)} / {MEM}")

    if "--phase2" in __import__("sys").argv:
        all_seeds = set(SEEDS) | set(dist1.keys())
        dist2, _ = bfs(sorted(all_seeds), "Phase 2 fixpoint (all discovered values as seeds)",
                       max_depth=3)
        missing = [TARGETS[t] for t in TARGETS if t not in dist2]
        print("still missing after phase 2:", missing or "NONE")

if __name__ == "__main__":
    main()
