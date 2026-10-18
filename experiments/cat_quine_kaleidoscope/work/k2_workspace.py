#!/usr/bin/env python3
"""K2 workspace map: safe cells, snapshot values, rails, C-entry state."""
import json
from pathlib import Path

N = 59049
P9 = [1, 9, 81, 729, 6561]
CT9 = (
    (4, 3, 3, 1, 0, 0, 1, 0, 0), (4, 3, 5, 1, 0, 2, 1, 0, 2),
    (5, 5, 4, 2, 2, 1, 2, 2, 1), (4, 3, 3, 1, 0, 0, 7, 6, 6),
    (4, 3, 5, 1, 0, 2, 7, 6, 8), (5, 5, 4, 2, 2, 1, 8, 8, 7),
    (7, 6, 6, 7, 6, 6, 4, 3, 3), (7, 6, 8, 7, 6, 8, 4, 3, 5),
    (8, 8, 7, 8, 8, 7, 5, 5, 4),
)
ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "experiments" / "cat_quine_kaleidoscope"


def crazy(x, y):
    return sum(CT9[y // P9[j] % 9][x // P9[j] % 9] * P9[j] for j in range(5))


def rot(x):
    return x // 3 + (x % 3) * 19683


def main():
    snap = {int(k): v for k, v in json.load(open(BASE / "evidence/M3_20261018/snap25445.json"))["mem_snapshot"].items()}
    tbl = {}
    with open(BASE / "evidence/M3_20261018/cell_table_f25976.txt") as f:
        next(f)
        for line in f:
            p = line.split()
            if len(p) == 7:
                tbl[int(p[0])] = tuple(int(x) for x in p[1:])
    safe = sorted(c for c, v in tbl.items() if v == (0, 0, 0, 0, 0, 0))

    def ranges(cells):
        out = []
        for c in cells:
            if out and c == out[-1][1] + 1:
                out[-1][1] = c
            else:
                out.append([c, c])
        return out

    print("safe ranges [0..400]:")
    for lo, hi in ranges([c for c in safe if c <= 400]):
        print(f"  [{lo}..{hi}] ({hi - lo + 1})")
    print("safe ranges [25000..26800]:")
    for lo, hi in ranges([c for c in safe if 25000 <= c <= 26800]):
        print(f"  [{lo}..{hi}] ({hi - lo + 1})")

    print("\nrotable/low values (snapshot):")
    for c in [0, 1, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 61, 117, 150,
              154, 155, 156, 187, 188, 25975, 25976, 26098, 26099, 26318, 26319,
              26407, 26408, 26409, 26412, 26413]:
        print(f"  mem[{c}] = {snap.get(c)}")

    print(f"\nrot(snap[187]) = {rot(snap[187])} (expect 19720)")
    print(f"rot(snap[154]) = {rot(snap[154])} (expect 26407)")

    print("\ncells 45..138 value histogram:")
    from collections import Counter
    cnt = Counter(snap[c] for c in range(45, 139))
    print(" ", dict(cnt))

    print("\nsnapshot cells holding values in [25646..25946]:")
    hits = [(c, snap[c]) for c in range(N) if 25646 <= snap[c] <= 25946]
    print(f"  {len(hits)} cells:", hits[:40])
    print("snapshot cells holding values in [25947..26413]:")
    hits2 = [(c, snap[c]) for c in range(N) if 25947 <= snap[c] <= 26413]
    print(f"  {len(hits2)} cells:", hits2[:40])
    print("snapshot cells holding 29524:")
    print(" ", [(c) for c in range(N) if snap[c] == 29524][:20])
    print("snapshot cells holding 0 in [0..300]:", [c for c in range(301) if snap[c] == 0])
    print("snapshot cells holding values in [33..126] (count):",
          sum(1 for c in range(N) if 33 <= snap[c] <= 126))

    print("\nC-entry check: safe low cells [34..127] and their snapshot values:")
    low = [c for c in safe if 34 <= c <= 127]
    print(" ", [(c, snap[c]) for c in low])


if __name__ == "__main__":
    main()
