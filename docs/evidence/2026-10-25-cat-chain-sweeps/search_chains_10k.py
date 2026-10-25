"""10,000-seed k=18 sweep with the only usable chain sweep enabled.

Same parameters as k18_attack/search_seeds_10k.py (borrow_penalty=1,
direct_gap=18, restart thresholds 0.80/0.90) but the synthesizer is
``chain_synth.py`` and the chain 58,890 -> 58,896 is enabled.  A chain link is
legal only when the value installed at the previous target equals the ``a``
required at the next one; both endpoints are solvable from the fill state and
the link is seed-independent.

Run: python3 docs/evidence/2026-10-25-cat-chain-sweeps/search_chains_10k.py
"""
import random
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from chain_synth import extract_target_state, synthesize_preamble_ops  # noqa: E402

REF = ROOT / "reference" / "malbolge_org" / "cat.mal"
CLEAN, HIGH, HD, _ = extract_target_state(REF, 9003)
TEMPLATE = [b for b in REF.read_bytes() if 33 <= b <= 126]
CHAIN = [58890, 58896]
BUDGET = 7213  # end_c = 99 + ops - 1 <= 9003 - 94*18


def run(seed: int) -> tuple[int, int]:
    ops = synthesize_preamble_ops(
        CLEAN, HIGH, HD, 9003,
        delta=94 * 18,
        template_clean=TEMPLATE,
        borrow_penalty=1,
        direct_gap=18,
        rng=random.Random(seed),
        restart_p1=0.80,
        restart_p2=0.90,
        chains=[CHAIN],
    )
    return seed, len(ops)


if __name__ == "__main__":
    with Pool(12) as pool:
        rows = pool.map(run, range(10000), chunksize=20)
    rows.sort(key=lambda r: r[1])
    print(
        "k18 pen1 0.80/0.90 all121 + chain 58890->58896: min",
        rows[0][1], "seed", rows[0][0],
        "best10", rows[:10],
        "fits", sum(1 for _, n in rows if n <= BUDGET),
    )
