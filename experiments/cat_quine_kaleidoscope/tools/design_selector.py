#!/usr/bin/env python3
"""design_selector.py - M3 selector design analysis.

Loads the state snapshot at the handoff (default: snap25445.json, c=25560,
d=155, a=20173) plus the phase-split cell table produced by
`trace_loop -f 25976 -T table` and reports the structure needed to place the
Q/C selector script:

  A. loop-phase dead cells (execB=0 and readB=0) = value-controllable by the
     handoff replacement script.
  B. deterministic `j` hop graph from a start cell; reachable set, landings on
     controllable cells, BFS paths.
  C. scans for pointer values of interest (cells holding 153, 26407, ...).
  D. per-address op decode helpers and char-for-op encoding.
  E. op(a, x) tables for candidate a in {81 ('Q'), 67 ('C')}.

Usage: design_selector.py <snap.json> <cell_table.txt> [start_d]
"""
import json
import sys

N = 59049
XLAT1 = "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha"
XLAT2 = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
CT = ((1, 0, 0), (1, 0, 2), (2, 2, 1))


def crazy_op(x, y):
    res, p = 0, 1
    for _ in range(10):
        res += CT[y % 3][x % 3] * p
        x //= 3
        y //= 3
        p *= 3
    return res


def rot_op(x):
    return (x // 3) + (x % 3) * 19683


def decode(a, opc):
    return XLAT1[(opc - 33 + a) % 94]


def char_for_op(a, op):
    for b in range(33, 127):
        if XLAT1[(b - 33 + a) % 94] == op:
            return b
    return None


def load_snap(path):
    snap = json.load(open(path))
    mem = [0] * N
    for k, v in snap["mem_snapshot"].items():
        mem[int(k)] = v
    return snap, mem


def load_table(path):
    tbl = {}
    with open(path) as f:
        next(f)
        for line in f:
            p = line.split()
            if len(p) != 7:
                continue
            c, ea, ra, wa, eb, rb, wb = (int(x) for x in p)
            tbl[c] = (ea, ra, wa, eb, rb, wb)
    return tbl


def hop_of(mem, x):
    return (mem[x] + 1) % N


def bfs_hops(mem, controllable, start, max_nodes=200):
    """BFS over deterministic hops; controllable cells have no forced edge
    (landing on one = stop of the deterministic chain)."""
    from collections import deque
    parent = {start: None}
    q = deque([start])
    order = []
    while q and len(parent) < max_nodes:
        x = q.popleft()
        if controllable.get(x):
            continue  # deterministic chain stops here (we choose next hop)
        y = hop_of(mem, x)
        if y not in parent:
            parent[y] = x
            q.append(y)
            order.append(y)
    return parent, order


def path_to(parent, x):
    p = []
    while x is not None:
        p.append(x)
        x = parent[x]
    return list(reversed(p))


def main():
    snap_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/opencode/snap25445.json"
    table_path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/opencode/cell_table.txt"
    start_d = int(sys.argv[3]) if len(sys.argv) > 3 else 155

    snap, mem = load_snap(snap_path)
    tbl = load_table(table_path)
    assert len(tbl) == N, f"table incomplete: {len(tbl)}"

    # A. controllable cells: in the running program, after the stub writes
    # them, nothing reads nor executes them in the loop phase.
    dead = [c for c in range(N) if tbl[c][3] == 0 and tbl[c][4] == 0]
    execB0 = [c for c in range(N) if tbl[c][3] == 0]
    print(f"== A. phase-B dead (execB=0 & readB=0): {len(dead)} cells")
    zones = []
    for c in dead:
        if zones and c == zones[-1][1] + 1:
            zones[-1][1] = c
        else:
            zones.append([c, c])
    for lo, hi in zones:
        print(f"  [{lo}..{hi}] ({hi-lo+1} cells)")
    deadset = set(dead)

    # cells that execute in phase B cannot be written; reads block too (handled
    # by deadset). To be thorough: writable = deadset minus executed ones.
    w_exec = [c for c in range(N) if tbl[c][3] > 0]
    print(f"  phase-B executed cells: {len(w_exec)}")

    # B. hop graph from start_d. fully deterministic through non-dead cells.
    contr = {c: True for c in deadset}
    parent, order = bfs_hops(mem, contr, start_d, max_nodes=5000)
    print(f"\n== B. hop BFS from d={start_d}: {len(parent)} reachable")
    cyc = None
    x = start_d
    seen = []
    while True:
        if contr.get(x):
            cyc = ("dead-landing", x)
            break
        y = hop_of(mem, x)
        if y in seen:
            cyc = ("cycle", y)
            break
        seen.append(x)
        x = y
    print("  deterministic chain:", " -> ".join(str(v) for v in seen[:20]))
    print("  ->", cyc)
    # dead landings reachable
    landings = [c for c in order if contr.get(c)]
    print(f"  dead landings on chain: {landings[:20]}")

    # C. pointer value scans
    print("\n== C. cells holding interesting values")
    interest = [152, 153, 154, 26407, 26408, 25975, 25947, 26003, 26206, 20173, 0, 1]
    holders = {v: [] for v in interest}
    for c in range(N):
        v = mem[c]
        if v in holders:
            holders[v].append(c)
    for v in interest:
        hs = holders[v]
        print(f"  value {v:5d}: {len(hs):3d} cells: {hs[:12]}{' ...' if len(hs) > 12 else ''}")
        for c in hs[:8]:
            ea, ra, wa, eb, rb, wb = tbl[c]
            print(f"      cell {c:6d}: execB={eb} readB={rb} writeB={wb}  {'DEAD' if c in deadset else ''}")

    # D. small helper demo
    print("\n== D. helpers")
    for a, op in [(25560, 'j'), (25560, '/'), (25561, 'p'), (25562, 'i'), (25976, 'i')]:
        print(f"  char_for_op({a}, {op!r}) = {char_for_op(a, op)} decodes to {decode(a, char_for_op(a, op))}")

    # E. op(a,x) tables for candidate old values
    print("\n== E. op(81,x) vs op(67,x) for candidate operands")
    cands = [152, 124, 20173, 29524, 98, 0]
    for x in cands:
        print(f"  x={x:6d}: op(81,x)={crazy_op(81,x):6d} (+1 = {crazy_op(81,x)+1 % N:6d})   "
              f"op(67,x)={crazy_op(67,x):6d} (+1 = {crazy_op(67,x)+1 % N:6d})")

    # extra: which dead cells are near the handoff region
    print("\n== extra: dead cells in [25550..25950]:")
    seg = [c for c in dead if 25550 <= c <= 25950]
    print(" ", seg)


if __name__ == "__main__":
    main()
