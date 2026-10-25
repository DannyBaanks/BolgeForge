"""Alignment map for multi-target chain sweeps (Classic Cat, all 121 targets).

A chain sweep writes several targets in one ascending d-walk, reusing the value
that the previous CRZ installed in `a`.  The link ``i -> j`` (address_i <
address_j) is legal iff::

    targ_i == find_a_for_crazy(cur_j, targ_j)

i.e. the value installed at target ``i`` is exactly the ``a`` required to write
target ``j`` in one CRZ.

The map is computed from the fill state (the crazy recurrence above the 9,382
cell image), which is the state the preamble sees before it touches a target.
Targets whose fill value has no CRZ preimage cannot be linked at all: they are
pre-cleared by the window strategy first, which changes their value.

Run: python3 docs/evidence/2026-10-25-cat-chain-sweeps/alignment_map.py
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from chain_synth import (  # noqa: E402
    MEM_SIZE,
    crazy_op,
    extract_target_state,
    find_a_for_crazy,
)

REF = ROOT / "reference" / "malbolge_org" / "cat.mal"
LIN_END = 9003

CLEAN, HIGH, HD, _ = extract_target_state(REF, LIN_END)
N = len(CLEAN)
ADDRS = sorted(HIGH)
MEM = list(CLEAN) + [0] * (MEM_SIZE - N)
for _i in range(N, MEM_SIZE):
    MEM[_i] = crazy_op(MEM[_i - 1], MEM[_i - 2])


def target_value(addr: int, delta: int) -> int:
    orig = HIGH[addr]
    return orig - delta if (LIN_END < orig < N) else orig


def rows_for(delta: int) -> list[tuple[int, int, int | None]]:
    return [(a, target_value(a, delta), find_a_for_crazy(MEM[a], target_value(a, delta))) for a in ADDRS]


print(f"targets={len(ADDRS)}  image={N}  handoff_d={HD}")
print()
print("k  delta  budget  usable_pairs  adjacent_pairs")
for k in range(15, 25):
    delta = 94 * k
    rows = rows_for(delta)
    usable = [
        (i, j)
        for i, ri in enumerate(rows)
        for j, rj in enumerate(rows)
        if i < j and rj[2] is not None and ri[1] == rj[2]
    ]
    adjacent = [p for p in usable if rows[p[1]][0] - rows[p[0]][0] == 1]
    print(f"{k:>2} {delta:>6} {8904 - delta:>7} {len(usable):>12} {len(adjacent):>14}")

print()
print("k=18 (delta=1692) alignment pairs and gaps:")
rows = rows_for(94 * 18)
usable = [
    (i, j)
    for i, ri in enumerate(rows)
    for j, rj in enumerate(rows)
    if i < j and rj[2] is not None and ri[1] == rj[2]
]
for i, j in usable:
    print(f"  {rows[i][0]} -> {rows[j][0]}  value={rows[i][1]:>5}  gap={rows[j][0] - rows[i][0]:>2}")

print()
print("k=18 targets that need a pre-clear (no CRZ preimage from fill):")
none = [r for r in rows if r[2] is None]
print(f"  {len(none)} of {len(rows)}: {[r[0] for r in none]}")
