#!/usr/bin/env python3
"""K2: decode instructions along candidate corridors + search 59048/729/1458 cells."""
import json
from pathlib import Path

N = 59049
XLAT1 = "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha"
ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "experiments" / "cat_quine_kaleidoscope"


def main():
    snap = {int(k): v for k, v in json.load(open(BASE / "evidence/M3_20261018/snap25445.json"))["mem_snapshot"].items()}
    data = (ROOT / "artifacts" / "candidate_m281_53562b.mal").read_bytes()
    T = [b for b in data if 33 <= b <= 126]  # image bytes (before selector edits)

    for target in (59048, 729, 1458, 29524, 0):
        cells = [c for c in range(N) if snap[c] == target]
        print(f"snapshot cells == {target}: {len(cells)} {cells[:12]}")

    def finstr(byte_index, addr):
        # instruction as decoded (value byte is the IMAGE byte at addr)
        if byte_index >= len(T):
            return "PAD"
        b = T[byte_index]
        return XLAT1[(b - 33 + addr) % 94]

    print("\ninstructions (image bytes) cells 0..60:")
    row = []
    for c in range(61):
        row.append(f"{c}:{finstr(c, c)}({T[c]})")
    print("  " + " ".join(row))

    print("\ninstructions cells 25555..25650:")
    for c in range(25555, 25651):
        print(f"  {c}: {finstr(c, c)}", end="")
        if c % 8 == 7:
            print()
    print()

    print("\ninstructions cells 25647..25946 (free block), first 60:")
    row = []
    for c in range(25647, 25707):
        row.append(f"{c}:{finstr(c, c)}")
    print("  " + " ".join(row))

    print("\ninstruction histogram in free block [25647..25946]:")
    from collections import Counter
    cnt = Counter(finstr(c, c) for c in range(25647, 25947))
    print(" ", dict(cnt))

    print("\ninstruction histogram in low zone [3..44]:")
    cnt2 = Counter(finstr(c, c) for c in range(3, 45))
    print(" ", {k: v for k, v in sorted(cnt2.items())})
    print("\nlow zone cells 3..44 instruction list:")
    for c in range(3, 45):
        print(f"  {c}: {finstr(c, c)}", end="")
        if c % 6 == 5:
            print()
    print()

    # what does cell 25947/25948 hold at snapshot?
    print("\nmem[25947] =", snap[25947], " mem[25948] =", snap[25948])
    print("values 25946..25950 cells:", [(c, snap[c]) for c in range(25944, 25952)])
    # find all cells holding values in free-block address range (any)
    hits = [(c, snap[c]) for c in range(N) if 25646 <= snap[c] <= 25945]
    print("cells holding free-block-range values:", hits)


if __name__ == "__main__":
    main()
