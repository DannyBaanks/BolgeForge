"""Splice the A* segment replacements into the compact boot and validate.

The A* paths (out_astar_segments.json) were found from the ORIGINAL boot
prefixes. After splicing earlier segments, later ones start from states whose
DEAD cells may differ, so a recorded path can break: every spliced segment is
re-validated at its checkpoint (same d, same a, same live-cell values); a
failing segment is re-searched with A* from the true current state.

Final equivalence gate: new boot + the ORIGINAL write-phase ops must reach
the exact final state of the original plan (a, d, full memory) — proving the
write plan is untouched.

Run: python3 docs/evidence/2026-10-25-cat-k19-frontier/boot_splice.py
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from constants import MEM_SIZE, crazy_op, rot_op  # noqa: E402
from tools.compact_boot import (  # noqa: E402
    CH_CRZ, CH_DLD, CH_ROT, build_compact_boot, planner_fill_mem,
    rebuild_orig_boot_ops,
)
from tools.resynthesize import extract_target_state, synthesize_preamble_ops  # noqa: E402
from boot_astar import astar  # noqa: E402

REF = ROOT / "reference" / "malbolge_org" / "cat.mal"


def apply_ops(mem, a, d, seq):
    for ch in seq:
        if ch == CH_DLD:
            d = mem[d]
        elif ch == CH_ROT:
            mem[d] = rot_op(mem[d])
            a = mem[d]
        elif ch == CH_CRZ:
            mem[d] = crazy_op(a, mem[d])
            a = mem[d]
        d = (d + 1) % MEM_SIZE
    return a, d


def main() -> None:
    clean, high_mods, hd, _ = extract_target_state(REF, 9003)
    template = [b for b in REF.read_bytes() if 33 <= b <= 126]
    n = len(clean)
    obo = rebuild_orig_boot_ops(template, n)
    boot_ops, _bm, _ba, _bd = build_compact_boot(obo, template, high_mods)
    boot = "".join(boot_ops)
    assert len(boot) == 1235

    segs = json.loads((HERE / "out_boot_segments.json").read_text())
    paths = json.loads((HERE / "out_astar_segments.json").read_text())
    replaced = sorted(
        ((segs[k]["boot_pos"], k) for k in paths if k in segs))
    print(f"replacements: {len(replaced)}")

    # chunks in order: (text, segname-or-None)
    chunks = []
    pos = 0
    for i, name in replaced:
        ln = segs[name]["len"]
        chunks.append((boot[pos:i], None))
        chunks.append((paths[name], name))
        pos = i + ln
    chunks.append((boot[pos:], None))

    # simulate with checkpoint validation; re-search failures
    mem = planner_fill_mem(template, n)
    a, d = 0, 1
    new_parts = []
    re_searched = []
    for text, name in chunks:
        if name is not None:
            info = segs[name]
            live = [c for c in info["live_end"] if c <= 96]
            ok = True
            m_probe = list(mem)
            a2, d2 = a, d
            try:
                a2, d2 = apply_ops(m_probe, a, d, text)
                assert (a2, d2) == (info["end_a"], info["end_d"])
                assert all(m_probe[c] == info["end_low"][c] for c in live)
            except AssertionError:
                ok = False
            if not ok:
                print(f"  {name}: recorded path broken from the new state -> re-search")
                goal_vals = {c: info["end_low"][c] for c in live}
                path, err = astar(
                    list(mem), a, d, info["end_d"], info["end_a"], live,
                    goal_vals, info["len"] - 1, 1_200_000)
                if path is not None:
                    print(f"  {name}: re-searched -> {len(path)} ops")
                    re_searched.append(name)
                    text = path
                    paths[name] = path
                else:
                    # the original text only reads live cells -> always valid
                    print(f"  {name}: re-search failed ({err}); keeping original")
                    paths.pop(name, None)
                    text = boot[info["boot_pos"]:info["boot_pos"] + info["len"]]
        a, d = apply_ops(mem, a, d, text)
        new_parts.append(text)
    new_boot = "".join(new_parts)
    assert d == 82, d
    print(f"new boot: {len(new_boot)} ops (was 1235); "
          f"re-searched: {re_searched or 'none'}")

    # original plan and its final state
    plan = synthesize_preamble_ops(
        clean, high_mods, hd, 9003, delta=94 * 18, template_clean=template,
        borrow_penalty=1, direct_gap=18, rng=random.Random(9803),
        restart_p1=0.80, restart_p2=0.90, boot="compact")
    assert len(plan) == 7199 and "".join(plan[:1235]) == boot
    write_ops = "".join(plan[1235:])
    mem_o = planner_fill_mem(template, n)
    a_f, d_f = apply_ops(mem_o, 0, 1, "".join(plan))

    # equivalence: new boot + original write ops == original final state
    mem_c = planner_fill_mem(template, n)
    a_c, d_c = apply_ops(mem_c, 0, 1, new_boot + write_ops)
    assert (a_c, d_c) == (a_f, d_f), ((a_c, d_c), (a_f, d_f))
    assert mem_c == mem_o, "final memory differs"
    print("EQUIVALENCE PASS: new boot + original write ops -> identical final state")

    (HERE / "out_boot_spliced.ops.txt").write_text(new_boot)
    (HERE / "out_astar_segments.json").write_text(json.dumps(paths, indent=1))
    total18 = len(new_boot) + len(write_ops)
    print(f"k=18 total: {total18} (budget 7213)")
    w19 = (HERE / "out_beam_k19s9330_ops.txt").read_text().strip()
    total19 = len(new_boot) + len(w19) + 1
    print(f"k=19 total: {total19} (budget 7119, margin {7119 - total19}) "
          f"[write stream: seed-9330 beam, {len(w19)} ops + JMP]")


if __name__ == "__main__":
    main()
