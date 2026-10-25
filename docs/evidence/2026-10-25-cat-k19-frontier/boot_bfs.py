"""Segment re-synthesis: BFS over real (a, d, mem) states with ops {o, j, *, p}.

The boot's verbatim segments predate route-awareness: they are raw reference
trajectory. Each segment is a pure (a, d, mem) program (no `i` ops anywhere
in the boot), so any segment can be replaced by ANY op sequence that reaches
its checkpoint: the same d, the same a, and the same values for the cells
that are live at the segment end (dead cells are free).

The search is a layered BFS with deduplication on (a, d, written-cell
delta); writes are forbidden outside cells < 1000 (the plan's own region and
the window must not be touched). A state cap and a depth cap bound the
search; the goal is any state matching the checkpoint.

Run:
  python3 docs/evidence/2026-10-25-cat-k19-frontier/boot_bfs.py            # all segments
  python3 docs/evidence/2026-10-25-cat-k19-frontier/boot_bfs.py --only A
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from constants import MEM_SIZE, crazy_op, rot_op  # noqa: E402
from tools.compact_boot import (  # noqa: E402
    CH_CRZ, CH_DLD, CH_NOP, CH_ROT, build_compact_boot,
    planner_fill_mem, rebuild_orig_boot_ops,
)
from tools.resynthesize import extract_target_state  # noqa: E402

REF = ROOT / "reference" / "malbolge_org" / "cat.mal"
MAX_WRITE_CELL = 999
OPS = (CH_NOP, CH_DLD, CH_ROT, CH_CRZ)


def sim(mem, a, d, seq):
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


def bfs_segment(start_mem, start_a, start_d, goal_d, goal_a, live_end,
                goal_vals, depth_cap, state_cap):
    """Layered BFS. live_end: cells that must equal goal_vals at the end.
    Returns the op string or None."""
    start_key = (start_a, start_d, ())
    frontier = {start_key: ""}
    # delta-key: (a, d, tuple of (cell, value) written so far, sorted)
    seen = {start_key}
    for depth in range(1, depth_cap + 1):
        nxt = {}
        for (a, d, delta), path in frontier.items():
            for ch in OPS:
                a2, d2 = a, d
                delta2 = delta
                if ch == CH_DLD:
                    d2 = start_mem[d] if d not in dict(delta) else dict(delta)[d]
                    d2 = (d2 + 1) % MEM_SIZE
                elif ch == CH_NOP:
                    d2 = (d + 1) % MEM_SIZE
                elif ch == CH_ROT:
                    if d > MAX_WRITE_CELL:
                        continue
                    v = dict(delta).get(d, start_mem[d])
                    v = rot_op(v)
                    a2 = v
                    dd = {c: v for c, _ in delta}
                    dd[d] = v
                    delta2 = tuple(sorted(dd.items()))
                    d2 = (d + 1) % MEM_SIZE
                else:  # CRZ
                    if d > MAX_WRITE_CELL:
                        continue
                    v = dict(delta).get(d, start_mem[d])
                    v = crazy_op(a2, v)
                    a2 = v
                    dd = {c: v for c, _ in delta}
                    dd[d] = v
                    delta2 = tuple(sorted(dd.items()))
                    d2 = (d + 1) % MEM_SIZE
                key = (a2, d2, delta2)
                if key in seen:
                    continue
                seen.add(key)
                p2 = path + ch
                # goal?
                if (d2 == goal_d and a2 == goal_a
                        and all(dict(delta2).get(c, start_mem[c]) == goal_vals[c]
                                for c in live_end)):
                    return p2
                nxt[key] = p2
        if not nxt:
            return None
        frontier = nxt
        if len(seen) > state_cap:
            return "CAP"
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="segment name prefix")
    ap.add_argument("--depth-cap", type=int, default=48)
    ap.add_argument("--state-cap", type=int, default=4_000_000)
    args = ap.parse_args()

    clean, high_mods, _hd, _ = extract_target_state(REF, 9003)
    template = [b for b in REF.read_bytes() if 33 <= b <= 126]
    n = len(clean)
    obo = rebuild_orig_boot_ops(template, n)
    boot_ops, _bm, _ba, _bd = build_compact_boot(obo, template, high_mods)
    boot = "".join(boot_ops)

    segs = json.loads((HERE / "out_boot_segments.json").read_text())
    total_before = total_after = 0
    for name, info in segs.items():
        if args.only and not name.startswith(args.only):
            continue
        i, ln = info["boot_pos"], info["len"]
        seg = boot[i:i + ln]
        # start state: simulate the boot prefix
        mem = planner_fill_mem(template, n)
        a, d = 0, 1
        for ch in boot[:i]:
            a, d = sim_step = None, None  # placeholder
        # (redo cleanly)
        a, d = 0, 1
        for ch in boot[:i]:
            if ch == CH_DLD:
                d = mem[d]
            elif ch == CH_ROT:
                mem[d] = rot_op(mem[d])
                a = mem[d]
            elif ch == CH_CRZ:
                mem[d] = crazy_op(a, mem[d])
                a = mem[d]
            d = (d + 1) % MEM_SIZE
        start_mem = list(mem)
        # end state (simulating the segment itself) and live values
        m2 = list(mem)
        a2, d2 = a, d
        for ch in seg:
            if ch == CH_DLD:
                d2 = m2[d2]
            elif ch == CH_ROT:
                m2[d2] = rot_op(m2[d2])
                a2 = m2[d2]
            elif ch == CH_CRZ:
                m2[d2] = crazy_op(a2, m2[d2])
                a2 = m2[d2]
            d2 = (d2 + 1) % MEM_SIZE
        goal_d, goal_a = d2, a2
        live_end = [c for c in info["live_end"] if c < 1000]
        goal_vals = {c: m2[c] for c in live_end}
        res = bfs_segment(start_mem, a, d, goal_d, goal_a, live_end, goal_vals,
                          min(args.depth_cap, ln - 1), args.state_cap)
        if res == "CAP":
            print(f"{name:14s} len {ln:3d} -> STATE CAP at depth {args.depth_cap}")
            total_before += ln
            total_after += ln
        elif res is None:
            print(f"{name:14s} len {ln:3d} -> no shorter path within depth {min(args.depth_cap, ln - 1)}")
            total_before += ln
            total_after += ln
        else:
            print(f"{name:14s} len {ln:3d} -> {len(res):3d} ops (saves {ln - len(res)})")
            total_before += ln
            total_after += len(res)
    print(f"TOTAL: {total_before} -> {total_after} (saves {total_before - total_after})")


if __name__ == "__main__":
    main()
