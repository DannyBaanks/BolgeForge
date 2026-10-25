"""A* re-synthesis of boot segments, with anchor creation.

The naive layered BFS (boot_bfs.py) explodes (4M states at depth 46 without
beating segment A). This version searches the same space with A*:

    h(state) = (#live cells whose current value != goal value)
             + dist_to_goal[d]   (reverse BFS on the start-memory d-graph)

Goal: same d, same a, same values for the live cells at the segment end
(dead cells free — the search may rotate/write them as jump anchors).
Ops {o, j, *, p}; parent links reconstruct the found path.

SAFETY (model vs real divergence): cells [99..1532] hold the encoded plan in
the real program but the reference image in the planner model. Reads (j) are
allowed only at d <= 98 or d >= 58,843 (model == real there); writes only at
d <= 96 (the boot's scratch region). `o` is always safe (no read).

Run:
  python3 docs/evidence/2026-10-25-cat-k19-frontier/boot_astar.py --only S8
  python3 docs/evidence/2026-10-25-cat-k19-frontier/boot_astar.py --big
"""
from __future__ import annotations

import argparse
import heapq
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
WRITE_MAX = 96
READ_MAX = 98
READ_HIGH = 58843
INF = 10 ** 9
OPS = (CH_NOP, CH_DLD, CH_ROT, CH_CRZ)


def read_safe(d: int) -> bool:
    return d <= READ_MAX or d >= READ_HIGH


def segment_states(boot, template, n, i, ln):
    mem = planner_fill_mem(template, n)
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
    a2, d2 = a, d
    for ch in boot[i:i + ln]:
        if ch == CH_DLD:
            d2 = mem[d2]
        elif ch == CH_ROT:
            mem[d2] = rot_op(mem[d2])
            a2 = mem[d2]
        elif ch == CH_CRZ:
            mem[d2] = crazy_op(a2, mem[d2])
            a2 = mem[d2]
        d2 = (d2 + 1) % MEM_SIZE
    return start_mem, a, d, a2, d2, mem  # mem mutated to the END state


def astar(start_mem, a0, d0, goal_d, goal_a, live, goal_vals, max_len, cap):
    # reverse d-graph distances (start memory)
    rev_jump = {}
    for x in range(0, 1000):
        if not read_safe(x):
            continue
        t = (start_mem[x] + 1) % MEM_SIZE
        rev_jump.setdefault(t, []).append(x)
    dist = {goal_d: 0}
    frontier = [goal_d]
    while frontier:
        nxt = []
        for g in frontier:
            dg = dist[g]
            x = (g - 1) % MEM_SIZE
            if x not in dist and x <= READ_MAX:
                dist[x] = dg + 1
                nxt.append(x)
            for x2 in rev_jump.get(g, ()):
                if x2 not in dist:
                    dist[x2] = dg + 1
                    nxt.append(x2)
        frontier = nxt
    if d0 not in dist:
        return None, "start unreachable to goal"

    wrong_start = [c for c in live if start_mem[c] != goal_vals[c]]
    right_start = [c for c in live if start_mem[c] == goal_vals[c]]

    def mism(delta):
        m = 0
        for c in wrong_start:
            if delta.get(c, start_mem[c]) != goal_vals[c]:
                m += 1
        for c in right_start:
            if c in delta and delta[c] != goal_vals[c]:
                m += 1
        return m

    def is_goal(a, d, delta):
        return (d == goal_d and a == goal_a and mism(delta) == 0)

    start_key = (a0, d0, ())
    g_of = {start_key: 0}
    parent = {start_key: None}
    heap = [(mism({}) + dist[d0], 0, start_key)]
    closed = set()
    expansions = 0
    while heap:
        f, g, key = heapq.heappop(heap)
        if key in closed:
            continue
        closed.add(key)
        a3, d3, delta_t = key
        delta = dict(delta_t)
        if is_goal(a3, d3, delta):
            path = []
            k = key
            while parent[k] is not None:
                pk, ch = parent[k]
                path.append(ch)
                k = pk
            return "".join(reversed(path)), None
        if len(closed) > cap:
            return None, f"CAP after {expansions} expansions"
        if g >= max_len:
            continue
        expansions += 1
        for ch in OPS:
            a4, d4 = a3, d3
            delta4 = delta
            if ch == CH_NOP:
                d4 = (d3 + 1) % MEM_SIZE
            elif ch == CH_DLD:
                if not read_safe(d3):
                    continue
                d4 = (delta.get(d3, start_mem[d3]) + 1) % MEM_SIZE
            elif ch == CH_ROT:
                if d3 > WRITE_MAX:
                    continue
                v = rot_op(delta.get(d3, start_mem[d3]))
                a4 = v
                delta4 = dict(delta)
                delta4[d3] = v
                d4 = (d3 + 1) % MEM_SIZE
            else:
                if d3 > WRITE_MAX:
                    continue
                v = crazy_op(a3, delta.get(d3, start_mem[d3]))
                a4 = v
                delta4 = dict(delta)
                delta4[d3] = v
                d4 = (d3 + 1) % MEM_SIZE
            g2 = g + 1
            if g2 > max_len:
                continue
            key2 = (a4, d4, delta_t if delta4 is delta
                    else tuple(sorted(delta4.items())))
            if g2 < g_of.get(key2, INF):
                g_of[key2] = g2
                parent[key2] = (key, ch)
                h2 = dist.get(d4, INF // 2)
                if h2 < INF // 2:
                    heapq.heappush(heap, (g2 + mism(delta4) + h2, g2, key2))
                else:
                    heapq.heappush(heap, (g2 + mism(delta4) + h2, g2, key2))
    return None, f"exhausted ({expansions} expansions)"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--big", action="store_true")
    ap.add_argument("--cap", type=int, default=1_200_000)
    args = ap.parse_args()

    clean, high_mods, _hd, _ = extract_target_state(REF, 9003)
    template = [b for b in REF.read_bytes() if 33 <= b <= 126]
    n = len(clean)
    obo = rebuild_orig_boot_ops(template, n)
    boot_ops, _bm, _ba, _bd = build_compact_boot(obo, template, high_mods)
    boot = "".join(boot_ops)
    segs = json.loads((HERE / "out_boot_segments.json").read_text())
    wanted = {"A", "C3", "S8", "C9", "L9c", "L10b"} if args.big else None

    total_before = total_after = 0
    found = {}
    for name, info in segs.items():
        key = name.split()[0]
        if args.only and key != args.only:
            continue
        if wanted is not None and key not in wanted:
            continue
        i, ln = info["boot_pos"], info["len"]
        if info.get("literal"):
            seg = boot[i:i + ln]
            start_mem, a0, d0, goal_a, goal_d, end_mem = segment_states(
                boot, template, n, i, ln)
            assert "".join(boot_ops)[i:i + ln] == seg
        else:
            start_mem, a0, d0, goal_a, goal_d, end_mem = segment_states(
                boot, template, n, i, ln)
        live = [c for c in info["live_end"] if c <= WRITE_MAX]
        goal_vals = {c: end_mem[c] for c in live}
        path, err = astar(start_mem, a0, d0, goal_d, goal_a, live, goal_vals,
                          ln - 1, args.cap)
        if path is not None:
            print(f"{name:14s} len {ln:3d} -> {len(path):3d} ops "
                  f"(saves {ln - len(path)})")
            found[name] = path
            total_before += ln
            total_after += len(path)
        else:
            print(f"{name:14s} len {ln:3d} -> no improvement: {err}")
            total_before += ln
            total_after += ln
    print(f"TOTAL: {total_before} -> {total_after} "
          f"(saves {total_before - total_after})")
    if found:
        (HERE / "out_astar_segments.json").write_text(json.dumps(found, indent=1))
        print("paths written -> out_astar_segments.json")


if __name__ == "__main__":
    main()
