"""Diagnose the splice divergence: find the first chunk where the new boot's
(a, d) leaves the original trajectory, and the cells responsible.

Simulates the original boot and the spliced boot in lockstep over the chunk
structure; at every ORIGINAL (non-replaced) chunk it asserts that (a, d)
matches the original trajectory at the corresponding position. The first
failing chunk pinpoints the splice that contaminated a cell the original
ops read (which would mean a liveness hole); the cell diff is printed.
"""
from __future__ import annotations

import json
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
from tools.resynthesize import extract_target_state  # noqa: E402

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
    clean, high_mods, _hd, _ = extract_target_state(REF, 9003)
    template = [b for b in REF.read_bytes() if 33 <= b <= 126]
    n = len(clean)
    obo = rebuild_orig_boot_ops(template, n)
    boot_ops, _bm, _ba, _bd = build_compact_boot(obo, template, high_mods)
    boot = "".join(boot_ops)

    segs = json.loads((HERE / "out_boot_segments.json").read_text())
    paths = json.loads((HERE / "out_astar_segments.json").read_text())
    replaced = sorted((segs[k]["boot_pos"], k) for k in paths if k in segs)
    print(f"replacements on disk: {len(replaced)}")

    # original trajectory states: (a, d) after each op
    mem_o = planner_fill_mem(template, n)
    orig_after = []
    a, d = 0, 1
    for ch in boot:
        a, d = apply_ops(mem_o, a, d, ch)
        orig_after.append((a, d))

    # build chunks exactly like boot_splice
    chunks = []
    pos = 0
    for i, name in replaced:
        ln = segs[name]["len"]
        chunks.append((boot[pos:i], None, pos))
        chunks.append((paths[name], name, i))
        pos = i + ln
    chunks.append((boot[pos:], None, pos))

    mem_c = planner_fill_mem(template, n)
    a, d = 0, 1
    for text, name, orig_pos in chunks:
        a_prev, d_prev = a, d
        mem_prev = list(mem_c)
        a, d = apply_ops(mem_c, a, d, text)
        end_pos = orig_pos + len(text) - 1
        if name is None and len(text) > 0:
            exp = orig_after[end_pos]
            if (a, d) != exp:
                print(f"DIVERGED in original chunk starting at boot[{orig_pos}] "
                      f"(len {len(text)}): after it (a,d)=({a},{d}), "
                      f"expected {exp}")
                # re-simulate from the true chain state to find the exact op
                m2 = list(mem_prev)
                a2, d2 = a_prev, d_prev
                for off, ch in enumerate(text):
                    a2, d2 = apply_ops(m2, a2, d2, ch)
                    if (a2, d2) != orig_after[orig_pos + off]:
                        print(f"  first diverging op at chunk offset {off} "
                              f"(boot[{orig_pos + off}]) op={ch!r} at d={d_prev if off==0 else None}: "
                              f"(a,d)=({a2},{d2}) expected {orig_after[orig_pos + off]}")
                        # cells that differ from the ORIGINAL trajectory here
                        m3 = planner_fill_mem(template, n)
                        a3, d3 = 0, 1
                        for ch3 in boot[:orig_pos + off + 1]:
                            a3, d3 = apply_ops(m3, a3, d3, ch3)
                        diff_cells = [c for c in range(0, 100) if m3[c] != m2[c]]
                        print(f"  low cells differing from the original trajectory: {diff_cells}")
                        return
                print("  (no single-op divergence found?!)")
                return
        if name is not None:
            info = segs[name]
            live = [c for c in info["live_end"] if c <= 96]
            bad = [c for c in live if mem_c[c] != info["end_low"][c]]
            status = "OK" if ((a, d) == (info["end_a"], info["end_d"]) and not bad) else "BROKEN"
            print(f"  spliced {name}: len {len(text)} -> {status}"
                  + (f" bad cells {bad}" if bad else ""))
            if status == "BROKEN":
                return
    print(f"chain complete: (a,d)=({a},{d})")


if __name__ == "__main__":
    main()
