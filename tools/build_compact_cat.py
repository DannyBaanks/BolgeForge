#!/usr/bin/env python3
"""Build the compact streaming Cat: handoff 9003, k=18, seeded restart 9803.

History: the generic search in ``tools/resynthesize.py`` stops at k=12 (8,254
cells).  A first seeded plan (k=15, seed 47, borrow penalty 2, direct window
jumps) fitted 7,443 preamble operations into the k=15 budget and published
7,972 cells (2026-10-24).  The k=15->k=18 frontier attack then measured that
the write phase repeats 5,964 operations for every k (the arithmetic of
``solve_sp``), so only the BOOT phase could pay for the larger shift: the
compact boot (``tools/compact_boot.py``, 1,235 ops instead of 1,367) removes
132 operations that the k=18 window plan never uses, and the seed-9803
restart plan lands at 7,199 operations — 14 under the 7,213 k=18 budget.
That yields 7,690 cells (282 fewer than the 7,972 build, 1,692 fewer than the
9,382-cell reference) with the reference handoff state intact (124/124
variables).  Evidence: ``docs/evidence/2026-10-25-compact-cat-k18/``.

Deterministic: fixed plan, fixed seed, fixed scan order.  Publication is gated by

  * ``tools.test_compressed.verify_target("cat", ...)`` exact-output cases;
  * ``tools/verify_handoff_state.py`` keep-high handoff comparison (124/124);
  * byte-exact rebuild in ``--check`` mode.

Usage:
  python3 tools/build_compact_cat.py            # rebuild, verify, publish
  python3 tools/build_compact_cat.py --check    # verify published bytes match
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.resynthesize import (
    REPO_ROOT,
    assemble_shifted_program,
    extract_target_state,
    synthesize_preamble_ops,
)
from tools.verify_handoff_state import (
    compare_handoff,
    load_program,
    memory_from_cells,
    run_to_cell,
)

SOURCE = REPO_ROOT / "reference" / "malbolge_org" / "cat.mal"
OUT_PATH = REPO_ROOT / "artifacts" / "cat_compact.mal"
LIN_END = 9003
# Reference loop entry used by the handoff gate (the '/' instruction the Cat reaches
# after its boot); the shifted candidate cell is REFERENCE_CELL - delta.
REFERENCE_CELL = 9067
PLAN = {
    "k": 18,
    "seed": 9803,
    "borrow_penalty": 1,
    "direct_gap": 18,
    "restart_p1": 0.80,
    "restart_p2": 0.90,
    "boot": "compact",
}


def build() -> tuple[bytes, dict]:
    clean, high_mods, handoff_d, _target = extract_target_state(SOURCE, LIN_END)
    template_clean = [b for b in SOURCE.read_bytes() if 33 <= b <= 126]
    delta = 94 * PLAN["k"]
    rng = random.Random(PLAN["seed"])
    ops = synthesize_preamble_ops(
        clean,
        high_mods,
        handoff_d,
        LIN_END,
        delta=delta,
        template_clean=template_clean,
        borrow_penalty=PLAN["borrow_penalty"],
        direct_gap=PLAN["direct_gap"],
        rng=rng,
        restart_p1=PLAN["restart_p1"],
        restart_p2=PLAN["restart_p2"],
        boot=PLAN["boot"],
    )
    raw, end_c = assemble_shifted_program(template_clean, ops, clean, LIN_END, delta)
    if raw is None:
        raise RuntimeError(f"plan does not fit: end_c={end_c} overruns handoff {LIN_END - delta}")
    info = {
        "context": str(SOURCE.relative_to(REPO_ROOT)),
        "plan": dict(PLAN),
        "delta": delta,
        "preamble_ops": len(ops),
        "end_c": end_c,
        "handoff_cell": LIN_END - delta,
        "pad_len": (LIN_END - delta) - end_c,
        "orig_cells": len(clean),
        "new_cells": len(raw),
        "saved_cells": len(clean) - len(raw),
    }
    return raw, info


def handoff_report(raw: bytes) -> dict:
    ref_cells, ref_mem = load_program(SOURCE)
    ref_init = list(ref_mem)
    cand_cells = [b for b in raw if 33 <= b <= 126]
    cand_mem = memory_from_cells(cand_cells)
    a_ref, c_ref, d_ref, _step_ref, status_ref = run_to_cell(ref_mem, REFERENCE_CELL)
    if status_ref != "AT_CELL":
        raise RuntimeError(f"reference never reached cell {REFERENCE_CELL}: {status_ref}")
    candidate_cell = REFERENCE_CELL - (94 * PLAN["k"])
    a_cand, c_cand, d_cand, _step_cand, status_cand = run_to_cell(cand_mem, candidate_cell)
    if status_cand != "AT_CELL":
        raise RuntimeError(f"candidate never reached cell {candidate_cell}: {status_cand}")
    return compare_handoff(
        reference_mem=ref_mem,
        reference_init=ref_init,
        reference_cells=len(ref_cells),
        candidate_mem=cand_mem,
        candidate_cells=len(cand_cells),
        delta=94 * PLAN["k"],
        reference_cell=c_ref,
        candidate_cell=c_cand,
        reference_regs=(a_ref, d_ref),
        candidate_regs=(a_cand, d_cand),
        value_floor=LIN_END,
        value_ceiling=len(ref_cells),
        memory_mode="keep-high",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="verify the published artifact instead of writing it")
    parser.add_argument("--json", type=Path, default=None, help="write the measurement report here")
    args = parser.parse_args(argv)

    from tools.test_compressed import verify_target

    raw, info = build()
    report = handoff_report(raw)
    if not report["ok"]:
        print("FAIL handoff: " + json.dumps(report["mismatches"][:3]), file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix="bolgeforge-compact-cat-") as directory:
        candidate = Path(directory) / OUT_PATH.name
        candidate.write_bytes(raw)
        cases = verify_target("cat", candidate)
    info["handoff"] = {
        "variables_installed": report["variables_installed"],
        "variables_total": report["variables_total"],
        "registers": report["registers"],
        "steps": {"reference_cell": REFERENCE_CELL},
    }

    if args.check:
        if OUT_PATH.read_bytes() != raw:
            print(f"FAIL {OUT_PATH.name}: published bytes differ from the deterministic rebuild", file=sys.stderr)
            return 1
        print(f"PASS cat_compact: {cases} cases; {len(raw)} cells; handoff 124/124; byte-exact rebuild")
    else:
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=OUT_PATH.parent, prefix=".verified-", delete=False) as staged:
            staged.write(raw)
            staged_path = Path(staged.name)
        # NamedTemporaryFile creates 0600; published artifacts use the repo's 0664.
        staged_path.chmod(0o664)
        staged_path.replace(OUT_PATH)
        print(f"PASS cat_compact: {cases} cases; {len(raw)} cells; handoff 124/124; published")
    print(json.dumps(info, sort_keys=True))
    if args.json:
        args.json.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
