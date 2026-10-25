"""Boot-shortening analysis: liveness + per-segment composition.

Goal: the compact boot (1,235 ops) must drop to <= 1,127 ops (-108) so the
best measured k=19 write phase (5,991 ops, seed 9330 + beam) fits the 7,119
budget. The boot contains no `i` ops (measured), so it is a pure (a, d, mem)
program and any verbatim segment can be re-synthesized with ops {o, j, *, p}.

This script:
  1. builds the full k=18 plan (canonical pipeline, 7,199 ops), logs every
     op's (d, write cell), and computes backward liveness of low cells
     (< 1000) across the whole plan, plus the write-phase planner reads;
  2. locates each verbatim segment inside the boot op stream;
  3. reports per segment: op composition, longest NOP run, dead stores
     (writes never read before overwritten), and the LIVE set at its end —
     the constraint any replacement must satisfy.

Run: python3 docs/evidence/2026-10-25-cat-k19-frontier/boot_analyze.py
"""
from __future__ import annotations

import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from constants import MEM_SIZE, crazy_op, rot_op  # noqa: E402
from tools.compact_boot import (  # noqa: E402
    CH_CRZ, CH_DLD, CH_JMP, CH_NOP, CH_ROT, build_compact_boot,
    planner_fill_mem, rebuild_orig_boot_ops,
)
from tools.resynthesize import extract_target_state, synthesize_preamble_ops  # noqa: E402

REF = ROOT / "reference" / "malbolge_org" / "cat.mal"
# cells the write-phase PLANNER reads besides what its ops read:
# spindle temp/x (35/36, 50/51, 73/74), odometer/anchors 82..96
PLANNER_READS = {35, 36, 50, 51, 73, 74, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96}

SEGS = [
    ("A    1..59", 1, 60),
    ("C3 111..152", 111, 153),
    ("S7 459..468", 459, 469),
    ("S8 485..567", 485, 568),
    ("L9a 622..629", 622, 630),
    ("L9b 663..684", 663, 685),
    ("L9c 752..794", 752, 795),
    ("L9d 849..870", 849, 871),
    ("L9e 932..947", 932, 948),
    ("C9 948..1005", 948, 1006),
    ("L10a 1006..1012", 1006, 1013),
    ("L10b 1020..1054", 1020, 1055),
    ("L10c 1099..1118", 1099, 1119),
    ("L10d 1163..1177", 1163, 1178),
    ("L10e 1219..1233", 1219, 1234),
    ("L10f 1275..1285", 1275, 1286),
    ("L11a 1342..1344", 1342, 1345),
    ("L11b 1352..1366", 1352, 1367),
]


def main() -> None:
    clean, high_mods, hd, _ = extract_target_state(REF, 9003)
    template = [b for b in REF.read_bytes() if 33 <= b <= 126]
    n = len(clean)
    obo = rebuild_orig_boot_ops(template, n)
    boot_ops, _bm, _ba, _bd = build_compact_boot(obo, template, high_mods)
    boot = "".join(boot_ops)
    assert len(boot) == 1235 and CH_JMP not in boot

    plan = synthesize_preamble_ops(
        clean, high_mods, hd, 9003, delta=94 * 18, template_clean=template,
        borrow_penalty=1, direct_gap=18, rng=random.Random(9803),
        restart_p1=0.80, restart_p2=0.90, boot="compact")
    assert len(plan) == 7199 and "".join(plan[:1235]) == boot

    # ---- per-op log ---------------------------------------------------------
    mem = planner_fill_mem(template, n)
    a, d = 0, 1
    log = []
    for ch in plan:
        w = None
        if ch == CH_DLD:
            d = mem[d]
        elif ch == CH_ROT:
            mem[d] = rot_op(mem[d])
            a = mem[d]
            w = d
        elif ch == CH_CRZ:
            mem[d] = crazy_op(a, mem[d])
            a = mem[d]
            w = d
        log.append((ch, d, w))
        d = (d + 1) % MEM_SIZE
    N = len(log)

    # ---- backward liveness: live[t] = cells whose value just before op t
    # must match the recorded plan for everything after t to be identical.
    live = [set() for _ in range(N + 1)]
    cur: set[int] = set()
    for t in range(N - 1, -1, -1):
        ch, dpos, w = log[t]
        if w is not None and w < 1000:
            cur.discard(w)          # op t overwrites cell w -> old value dead
        if dpos < 1000 and ch != CH_NOP:
            cur.add(dpos)           # op t reads mem[dpos] (j target / rot / crz)
        if t == 1235:
            cur |= PLANNER_READS    # planner reads sit at the boot boundary
        live[t] = set(cur)
    live[N] = set()

    print("== write phase low-cell footprint (ops 1235..) ==")
    r = sorted({dp for ch, dp, w in log[1235:] if dp < 1000 and ch != CH_NOP})
    wls = sorted({w for ch, dp, w in log[1235:] if w is not None and w < 1000})
    print(f"  reads : {r}")
    print(f"  writes: {wls}")
    print(f"  LIVE at boot end: {sorted(live[1235])}")

    # ---- per-segment report -------------------------------------------------
    print("== verbatim segments inside the boot stream ==")
    total_ops = 0
    pos = 0
    for name, s, e in SEGS:
        seg = "".join(obo[s:e])
        if name.startswith("S8"):
            seg = "".join(obo[s:515]) + CH_NOP + "".join(obo[524:e])
        i = boot.find(seg, pos)
        assert i >= 0, name
        pos = i + len(seg)
        cnt = Counter(seg)
        # dead stores inside the segment: writes whose value is not read later
        dead = 0
        for k in range(len(seg)):
            ch, dp, w = log[i + k]
            if w is not None and w < 1000 and w not in live[i + k + 1]:
                dead += 1
        # longest o-run
        best = cur_run = 0
        for ch in seg:
            cur_run = cur_run + 1 if ch == CH_NOP else 0
            best = max(best, cur_run)
        live_end = sorted(c for c in live[i + len(seg)] if c < 1000)
        total_ops += len(seg)
        print(f"{name:16s} boot[{i:4d}..{i + len(seg):4d}] ops {len(seg):3d} "
              f"o={cnt[CH_NOP]:3d} j={cnt[CH_DLD]:3d} *={cnt[CH_ROT]:3d} p={cnt[CH_CRZ]:3d} "
              f"maxNOPrun={best:2d} deadW={dead:2d} liveEnd={live_end}")
    print(f"total verbatim ops: {total_ops}")

    # checkpoint states for the shortener (dump)
    import json
    out = {}
    pos = 0
    for name, s, e in SEGS:
        seg = "".join(obo[s:e])
        if name.startswith("S8"):
            seg = "".join(obo[s:515]) + CH_NOP + "".join(obo[524:e])
        i = boot.find(seg, pos)
        pos = i + len(seg)
        # segment-start state and end-state live values, from a fresh sim
        m2 = planner_fill_mem(template, n)
        a2, d2 = 0, 1
        for ch in boot[:i]:
            if ch == CH_DLD:
                d2 = m2[d2]
            elif ch == CH_ROT:
                m2[d2] = rot_op(m2[d2]); a2 = m2[d2]
            elif ch == CH_CRZ:
                m2[d2] = crazy_op(a2, m2[d2]); a2 = m2[d2]
            d2 = (d2 + 1) % MEM_SIZE
        live_end = sorted(c for c in live[i + len(seg)] if c < 1000)
        out[name.strip()] = {
            "boot_pos": i, "len": len(seg),
            "start_d": d2, "start_a": a2,
            "start_low": [m2[c] for c in range(100)],
            "end_d": log[i + len(seg) - 1][1] if False else None,
            "live_end": live_end,
        }
        # end d: simulate the segment
        d3, a3 = d2, a2
        for ch in seg:
            if ch == CH_DLD:
                d3 = m2[d3]
            elif ch == CH_ROT:
                m2[d3] = rot_op(m2[d3]); a3 = m2[d3]
            elif ch == CH_CRZ:
                m2[d3] = crazy_op(a3, m2[d3]); a3 = m2[d3]
            d3 = (d3 + 1) % MEM_SIZE
        out[name.strip()]["end_d"] = d3
        out[name.strip()]["end_a"] = a3
        out[name.strip()]["end_low"] = [m2[c] for c in range(100)]
    (HERE / "out_boot_segments.json").write_text(json.dumps(out, indent=1))
    print("segment checkpoints dumped -> out_boot_segments.json")


if __name__ == "__main__":
    main()
