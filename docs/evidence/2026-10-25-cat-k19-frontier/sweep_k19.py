"""k=19 seed sweep: the write-ORDER lever at delta 1,786 (compact boot).

At k=18 the seeded order search was worth -312 ops vs the deterministic plan;
at k=19 the greedy order (seed 9803) costs 6,368 write ops and the fixed-order
beam ceiling is ~-192, so the budget (write <= 5,883) needs the order search
plus the beam together. This sweep measures the order landscape at k=19:
synthesizes the full preamble with the canonical pipeline
(tools.resynthesize, boot="compact") for seeds 0..N-1 and reports the best.

Run: python3 docs/evidence/2026-10-25-cat-k19-frontier/sweep_k19.py [--seeds 10000] [--workers 12]
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from tools.resynthesize import extract_target_state, synthesize_preamble_ops  # noqa: E402

REF = ROOT / "reference" / "malbolge_org" / "cat.mal"
K = 19
DELTA = 94 * K
BOOT_OPS = 1235
BUDGET = (9003 - DELTA) - 98          # 7119 total preamble ops allowed
WRITE_NEED = BUDGET - BOOT_OPS - 1   # 5883 (boot + JMP are fixed)

_STATE = None


def _init():
    global _STATE
    clean, high_mods, hd, _ = extract_target_state(REF, 9003)
    template = [b for b in REF.read_bytes() if 33 <= b <= 126]
    _STATE = (clean, high_mods, hd, template)


def _run(seed: int) -> tuple[int, int]:
    clean, high_mods, hd, template = _STATE
    ops = synthesize_preamble_ops(
        clean, high_mods, hd, 9003,
        delta=DELTA, template_clean=template,
        borrow_penalty=1, direct_gap=18,
        rng=random.Random(seed), restart_p1=0.80, restart_p2=0.90,
        boot="compact")
    return len(ops), seed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10000)
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()

    t0 = time.time()
    with Pool(args.workers, initializer=_init) as pool:
        results = []
        best = (10 ** 9, -1)
        fits = 0
        for i, (total, seed) in enumerate(pool.imap_unordered(_run, range(args.seeds), chunksize=20), 1):
            results.append((total, seed))
            if total < best[0]:
                best = (total, seed)
                print(f"  seed {seed}: total {total} (write {total - BOOT_OPS - 1}, "
                      f"need <= {WRITE_NEED})", flush=True)
            if total <= BUDGET:
                fits += 1
            if i % 500 == 0:
                print(f"  ... {i}/{args.seeds} seeds, best {best}, "
                      f"fits {fits}, {time.time() - t0:.0f}s", flush=True)

    results.sort()
    print(f"== sweep done: {args.seeds} seeds in {time.time() - t0:.0f}s ==")
    print(f"  best: seed {best[1]} total {best[0]} (write {best[0] - BOOT_OPS - 1})")
    print(f"  fits (total <= {BUDGET}): {fits}")
    print(f"  top 10: {results[:10]}")
    out = [{"seed": s, "total": t, "write": t - BOOT_OPS - 1} for t, s in results[:50]]
    (HERE / "out_sweep_k19.json").write_text(
        __import__("json").dumps(out, indent=1))


if __name__ == "__main__":
    main()
