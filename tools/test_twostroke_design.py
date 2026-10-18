#!/usr/bin/env python3
"""tools/test_twostroke_design.py - Test and design the Two-Stroke Period-2 Engine."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.trace_tm import op, rot, XLAT1, XLAT2

# Verify F <-> J permutation
assert XLAT2[70-33] == chr(74)
assert XLAT2[74-33] == chr(70)

# 1. Identify all mod-94 positions
active_positions = {}
nop_positions = []

for c in range(94):
    f_op = XLAT1[(70 - 33 + c) % 94]
    j_op = XLAT1[(74 - 33 + c) % 94]
    act_f = f_op in ['/', '<', 'i', 'j', 'p', '*', 'v']
    act_j = j_op in ['/', '<', 'i', 'j', 'p', '*', 'v']
    if act_f or act_j:
        active_positions[c] = (f_op, j_op)
    else:
        nop_positions.append(c)

print(f"Total positions: 94 | Active positions: {len(active_positions)} | Pure NOP positions: {len(nop_positions)}")
print("\nActive Mod-94 Positions:")
for c, (f_op, j_op) in sorted(active_positions.items()):
    print(f"  c % 94 = {c:2d} -> F = {f_op:2s} | J = {j_op:2s}")

assert len(nop_positions) == 80
print("\n>>> VERIFIED: 80 out of 94 positions are 100% inert NOPs under both F and J!")
