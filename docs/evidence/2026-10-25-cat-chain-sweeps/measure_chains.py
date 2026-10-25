"""Deterministic measurement of chain-sweep gains against the k=18 Cat plan.

Baseline: seed 9803 reproduces the published 7,331 operations; the
deterministic plan (rng=None) is 7,643.  A chain is emitted as a unit: the
first target pays the normal `solve_sp` + walk, the following targets pay only
the intervening NOPs plus one CRZ each, and the walk ends with a single return
to cell 82.

Run: python3 docs/evidence/2026-10-25-cat-chain-sweeps/measure_chains.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from chain_synth import extract_target_state, synthesize_preamble_ops  # noqa: E402

REF = ROOT / "reference" / "malbolge_org" / "cat.mal"
CLEAN, HIGH, HD, _ = extract_target_state(REF, 9003)
TEMPLATE = [b for b in REF.read_bytes() if 33 <= b <= 126]
DELTA = 94 * 18
BUDGET = 7213

FIVE = [58864, 58881, 58890, 58896, 58931]
PAIR = [58890, 58896]
PRECLEARED = [58884, 58893]  # 58,893 has no CRZ preimage from fill


def run(chains, seed=None, pen=1, gap=18):
    ops = synthesize_preamble_ops(
        CLEAN, HIGH, HD, 9003,
        delta=DELTA, template_clean=TEMPLATE,
        borrow_penalty=pen, direct_gap=gap,
        rng=random.Random(seed) if seed is not None else None,
        restart_p1=0.80, restart_p2=0.90,
        chains=chains,
    )
    return ops, synthesize_preamble_ops.write_trace, synthesize_preamble_ops.chain_trace


base_ops, base_trace, _ = run(None)
print(f"baseline deterministic : {len(base_ops)} ops  (budget {BUDGET})")

last = {}
for addr, targ, a_before, length, curr in base_trace:
    last[addr] = (targ, a_before, length, curr)
cost = {a: v[2] for a, v in last.items()}
print(f"per-write seq lengths  : {len(cost)} targets, sum {sum(cost.values())}")
print(f"  writes >= 25 ops     : {sum(1 for v in cost.values() if v >= 25)} "
      f"(sum {sum(v for v in cost.values() if v >= 25)})")
print(f"  writes <= 15 ops     : {sum(1 for v in cost.values() if v <= 15)} "
      f"(sum {sum(v for v in cost.values() if v <= 15)})")
print("  five chain targets   : " + ", ".join(f"{a}:{cost[a]}" for a in FIVE) +
      f"  (sum {sum(cost[a] for a in FIVE)})")

for label, chains in (("five-target chain", [FIVE]), ("pair 58890->58896", [PAIR])):
    ops, _tr, ct = run(chains)
    print(f"{label:22s}: {len(ops)} ops  delta {len(ops) - len(base_ops):+d}  emitted={ct}")

try:
    run([PRECLEARED])
except AssertionError as exc:
    print(f"pair 58884->58893      : invalid at chain time (needs pre-clear): {exc}")

seed_ops, _tr, _ct = run(None, seed=9803)
print(f"baseline seed 9803     : {len(seed_ops)} ops  (published frontier 7331)")
seed_ops, _tr, _ct = run([PAIR], seed=9803)
print(f"pair seed 9803         : {len(seed_ops)} ops")
