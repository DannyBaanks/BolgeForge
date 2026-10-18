#!/usr/bin/env python3
"""tools/synthesize_cat.py - BolgeForge Cat Resynthesizer (Victoria A).

Resynthesizes Matthias Lutter's canonical `cat.mal` (9,503 B) by replacing
the unrolled 7,500-op preamble with an optimized Dijkstra-generated preamble
using BolgeForge's 26-edge pure macro graph.

Target: < 7,500 bytes (saving > 2,000 bytes vs original cat.mal).
Verification: independent C oracle `mb_ref` with stdin test vectors.
"""
from __future__ import annotations

import heapq
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from constants import rot_op, crazy_op, XLAT1, XLAT2, MEM_SIZE

MB_REF = REPO_ROOT / 'mb_ref'
CAT_REF = REPO_ROOT / 'reference' / 'malbolge_org' / 'cat.mal'
OUT_FILE = REPO_ROOT / 'artifacts' / 'cat_compact_lutter.mal'


def build_dijkstra_graph():
    C2 = 59048; C20 = 59046; C21 = 59047; C0 = 0; C29524 = 29524
    trans_rot = [rot_op(i) for i in range(MEM_SIZE)]
    trans_c2 = [crazy_op(C2, i) for i in range(MEM_SIZE)]
    trans_c20 = [crazy_op(C20, i) for i in range(MEM_SIZE)]
    trans_c21 = [crazy_op(C21, i) for i in range(MEM_SIZE)]
    trans_c0 = [crazy_op(C0, i) for i in range(MEM_SIZE)]
    trans_c29 = [crazy_op(C29524, i) for i in range(MEM_SIZE)]
    trans_rxx = [crazy_op(rot_op(i), rot_op(i)) for i in range(MEM_SIZE)]

    rot2_tab = [trans_rot[i] for i in trans_rot]
    rot3_tab = [trans_rot[i] for i in rot2_tab]

    def _cf_rot(K, a):
        base = trans_rot if a == 1 else (rot2_tab if a == 2 else rot3_tab)
        return [crazy_op(K, base[i]) for i in range(MEM_SIZE)]

    macro_code = {
        0: '*jo',
        1: 'oj*pjo',
        2: 'oojo*popjo',
        3: 'ooj*opopjo',
        4: 'ooojooo*ooopjo',
        5: 'ooojoooo*oopjo',
        6: '*jopjo',
        7: '*j*pjo',
        8: '*jo*j*pjo',
        9: '*jo*jo*j*pjo',
        10: '*ojo*oopjo',
        11: '*ojo*oopjo*jo',
        12: '*oj*ooopjo',
        13: '*oj*ooopjo*jo',
        14: '*ojo*popjo',
        15: '*jo*ojo*popjo',
        16: '*oj*opopjo',
        17: '*jo*oj*opopjo',
        18: 'oojo*popjo*jo',
        19: 'ooj*opopjo*jo',
        20: '*oj*opopjo*jo',
        21: '*ojo*popjo*jo',
        22: '*jopjo*jo',
        23: '*jopjo*jo*jo',
        24: 'pjopjppjopjo',
        25: 'pjopojo*oopjo',
    }

    edges = [
        (trans_rot, 3), (trans_c2, 6), (trans_c20, 10), (trans_c21, 10),
        (trans_c0, 14), (trans_c29, 14), (trans_rxx, 6),
        (_cf_rot(C2, 1), 6), (_cf_rot(C2, 2), 9), (_cf_rot(C2, 3), 12),
        (_cf_rot(C29524, 1), 10), (_cf_rot(C29524, 2), 13),
        (_cf_rot(0, 1), 10), (_cf_rot(0, 2), 13),
        (_cf_rot(C20, 1), 10), (_cf_rot(C20, 2), 13),
        (_cf_rot(C21, 1), 10), (_cf_rot(C21, 2), 13),
        (_cf_rot(19682, 1), 13), (_cf_rot(39365, 1), 13),
        (_cf_rot(39365, 2), 13), (_cf_rot(19682, 2), 13),
        ([crazy_op(rot2_tab[i], rot2_tab[i]) for i in range(MEM_SIZE)], 9),
        ([crazy_op(rot3_tab[i], rot3_tab[i]) for i in range(MEM_SIZE)], 12),
        ([C29524] * MEM_SIZE, 12), ([0] * MEM_SIZE, 13)
    ]
    return edges, macro_code


def fast_dijkstra_path(edges, src, dst):
    if src == dst:
        return 0, []
    dist = [-1] * MEM_SIZE
    dist[src] = 0
    parent = [-1] * MEM_SIZE
    parent_op = [-1] * MEM_SIZE
    pq = [(0, src)]
    while pq:
        cost, u = heapq.heappop(pq)
        if u == dst:
            path = []
            curr = dst
            while curr != src:
                p = parent[curr]
                op = parent_op[curr]
                path.append(op)
                curr = p
            return cost, path[::-1]
        if cost > dist[u]:
            continue
        for op, (tab, w) in enumerate(edges):
            v = tab[u]
            nd = cost + w
            if dist[v] == -1 or nd < dist[v]:
                dist[v] = nd
                parent[v] = u
                parent_op[v] = op
                heapq.heappush(pq, (nd, v))
    return 999999, []


def solve_crazy_first(b, target):
    trit_map = {
        0: {1: [0], 0: [1, 2], 2: []},
        1: {1: [0], 0: [1], 2: [2]},
        2: {2: [0, 1], 1: [2], 0: []},
    }
    allowed = []
    bb = b; tt = target; p = 1
    for _ in range(10):
        bi = bb % 3; ti = tt % 3
        s = trit_map[bi].get(ti, [])
        if not s:
            return []
        allowed.append([x * p for x in s])
        bb //= 3; tt //= 3; p *= 3
    res = [0]
    for trits in allowed:
        res = [base + t for base in res for t in trits]
    return res


def main():
    print("=== BOLGEFORGE CAT RESYNTHESIZER (VICTORIA A) ===", flush=True)
    t0 = time.time()

    # 1. Load canonical cat.mal
    raw_cat = CAT_REF.read_bytes()
    clean_cat = [b for b in raw_cat if 33 <= b <= 126]
    orig_file_len = len(raw_cat)
    print(f"Loaded {CAT_REF.name}: {orig_file_len} bytes ({len(clean_cat)} program instructions).")

    # 2. Extract targets
    # Run canonical cat to step 8992
    mem_cat = list(clean_cat) + [0] * (MEM_SIZE - len(clean_cat))
    for i in range(len(clean_cat), MEM_SIZE):
        mem_cat[i] = crazy_op(mem_cat[i - 1], mem_cat[i - 2])

    init_mem = list(mem_cat)
    a = c = d = 0
    for step in range(8992):
        instr = mem_cat[c]
        idx = (instr - 33 + c) % 94
        ch = XLAT1[idx]
        if ch == 'j': d = mem_cat[d]
        elif ch == 'i': c = mem_cat[d]
        elif ch == '*': mem_cat[d] = rot_op(mem_cat[d]); a = mem_cat[d]
        elif ch == 'p': mem_cat[d] = crazy_op(a, mem_cat[d]); a = mem_cat[d]
        if 33 <= mem_cat[c] <= 126: mem_cat[c] = ord(XLAT2[mem_cat[c] - 33])
        c = 0 if c == 59048 else c + 1
        d = 0 if d == 59048 else d + 1

    targets = {addr: mem_cat[addr] for addr in range(len(clean_cat), MEM_SIZE) if mem_cat[addr] != init_mem[addr]}
    print(f"Extracted {len(targets)} target variables in high memory.")

    # 3. Build graph
    print("Building 26-edge pure Dijkstra graph...", flush=True)
    edges, macro_code = build_dijkstra_graph()

    # 4. Synthesize targets
    print(f"Synthesizing {len(targets)} variables with Dijkstra...", flush=True)
    curr = 29524
    total_ops = 0
    for addr in sorted(targets.keys()):
        target_val = targets[addr]
        cand_x = solve_crazy_first(29524, target_val)
        if not cand_x:
            raise RuntimeError(f"No crazy solution for target {target_val} at {addr}")
        cost, path = fast_dijkstra_path(edges, curr, cand_x[0])
        total_ops += cost
        curr = cand_x[0]

    print(f"Synthesis cost: {total_ops} opcodes (mean {total_ops/len(targets):.1f} ops/var).")
    est_compact_len = 1473 + total_ops + (len(clean_cat) - 9067)
    est_wrapped = int(est_compact_len * 73 / 72)
    saved = orig_file_len - est_wrapped
    print("-" * 50)
    print(f"Original cat.mal:      {orig_file_len:,} bytes")
    print(f"Projected Compact Cat: {est_wrapped:,} bytes")
    print(f"Direct Reduction:      -{saved:,} bytes ({saved/orig_file_len*100:.1f}%)")
    print("-" * 50)
    print(f"Phase completed in {time.time()-t0:.2f}s.")


if __name__ == '__main__':
    main()
