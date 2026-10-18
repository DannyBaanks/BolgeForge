#!/usr/bin/env python3
"""K2 recovery search.

Goal: find F = sequence of transforms (rot(D[d]) via '*', and p against
operand-cells whose value chooses a digitwise row-map O[r]) such that
  F(op(b, H)) & 255 == b   for all b in 0..255
where H is the value held by the store cell at first use.

Transforms available per step (value-level):
  ROT   : v -> v//3 + (v%3)*19683
  ROW[r]: v -> digitwise O[r][digit_j]
"""
import json
from pathlib import Path
from collections import deque

N = 59049
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
P9 = [1, 9, 81, 729, 6561]


def op(x, y):
    i = 0
    for j in range(5):
        i += O[(y // P9[j]) % 9][(x // P9[j]) % 9] * P9[j]
    return i


def rot(v):
    return v // 3 + (v % 3) * 19683


def rowmap(r, v):
    i = 0
    for j in range(5):
        i += O[r][(v // P9[j]) % 9] * P9[j]
    return i


TILES = [("ROT", rot)] + [(f"R{r}", (lambda rr: (lambda v: rowmap(rr, v)))(r)) for r in range(9)]


def bfs(start_vec):
    target = tuple(range(256))
    start = tuple(start_vec)
    if start == target:
        return []
    prev = {start: None}
    q = deque([start])
    while q:
        s = q.popleft()
        for name, fn in TILES:
            ns = tuple(fn(v) for v in s)
            if ns not in prev:
                prev[ns] = (s, name)
                if ns == target:
                    path = []
                    cur = ns
                    while prev[cur] is not None:
                        cur, nm = prev[cur]
                        path.append(nm)
                    return path[::-1]
                q.append(ns)
    return None


def main():
    for H in (29524, 0):
        start = [op(b, H) for b in range(256)]
        path = bfs(start)
        print(f"H={H}: path = {path}")
        if path:
            # verify
            ok = True
            for b in range(256):
                v = op(b, H)
                for nm in path:
                    if nm == "ROT":
                        v = rot(v)
                    else:
                        v = rowmap(int(nm[1:]), v)
                if (v & 255) != b:
                    ok = False
                    break
            print("   verify:", ok)
        # also count reachable states
    # extra: start = op(row0(b), 29524) i.e. store after a pre-row0
    for H, pre in ((29524, "R0"), (0, "R0"), (29524, "R4"), (0, "R4")):
        start = []
        for b in range(256):
            v = op(b, H)
            if pre == "R0":
                v = rowmap(0, v)
            else:
                v = rowmap(4, v)
            start.append(v)
        path = bfs(start)
        print(f"H={H} pre={pre}: path = {path}")


if __name__ == "__main__":
    main()


def search_rotated():
    for H in (29524, 121, 0):
        for m in range(10):
            start = []
            for b in range(256):
                v = op(b, H)
                for _ in range(m):
                    v = rot(v)
                start.append(v)
            path = bfs(start)
            if path is not None:
                print(f"H={H} m={m}: F={path}")
    print("search_rotated done")


if __name__ == "__main__":
    search_rotated()
