"""k=19 frontier, decisive experiment: real-state beam over spindle assignment.

The demand sequence (out_demand.json, extracted by w1_demand.py from the
published 7,199-op k=18 plan) fixes the write ORDER. This script replays that
order on the real machine state, choosing per write which spindle
(33/48/71) and which entry (live-a / zero-a) to use:

  control mode (default): the greedy rule of the synthesizer (per spindle
    min(s1, s2), then min length + borrow penalty, first-wins ties) must
    reproduce the recorded write phase EXACTLY — every recorded write length
    must match and the total must be 5,963 (+1 handoff JMP = 5,964). This
    validates the replay before any beam result is trusted.

  beam mode: all 6 candidates per write, states deduplicated by
    (low memory 30..99, a), best-B by cost. The result is a REAL plan (the
    winner's op stream is written out), not a cost model. k=19 needs the
    write phase <= 5,884 ops, i.e. beam total <= 5,883 (budget 7,119 minus
    boot 1,235 minus the JMP).

Run:
  python3 docs/evidence/2026-10-25-cat-k19-frontier/w2_beam.py            # control
  python3 docs/evidence/2026-10-25-cat-k19-frontier/w2_beam.py --beam 32
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
K18 = ROOT / "docs" / "evidence" / "2026-10-25-cat-chain-sweeps"
K18EV = ROOT / "docs" / "evidence" / "2026-10-25-compact-cat-k18"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(K18))
sys.path.insert(0, str(K18EV))
sys.path.insert(0, str(HERE))

from constants import (  # noqa: E402
    MEM_SIZE, OP_CHAR_MAP, OP_CRAZY, OP_DLOAD, OP_JMP, OP_NOP, OP_ROT,
    XLAT1, XLAT2, crazy_op, rot_op,
)
import chain_synth as CS  # noqa: E402
from tools.compact_boot import build_compact_boot, rebuild_orig_boot_ops  # noqa: E402

REF = ROOT / "reference" / "malbolge_org" / "cat.mal"
LIN_END = 9003
C29524, C59048 = 29524, 59048
CH_NOP = OP_CHAR_MAP[OP_NOP]
CH_ROT = OP_CHAR_MAP[OP_ROT]
CH_CRZ = OP_CHAR_MAP[OP_CRAZY]
CH_DLD = OP_CHAR_MAP[OP_DLOAD]
CH_JMP = OP_CHAR_MAP[OP_JMP]

ALL_SPS = (
    (33, CH_NOP * 2 + CH_DLD, CH_ROT + CH_NOP + CH_DLD),
    (71, CH_NOP * 3 + CH_DLD, CH_ROT + CH_NOP * 2 + CH_DLD),
    (48, CH_NOP * 4 + CH_DLD, CH_ROT + CH_NOP * 3 + CH_DLD),
)
RESET_94_SEQ = (
    CH_NOP * 2 + CH_DLD + CH_ROT + CH_NOP * 5 + CH_DLD
    + CH_CRZ + CH_DLD + CH_NOP * 6 + CH_CRZ + CH_NOP + CH_DLD
)


def new_state(mem, a, d):
    return {"mem": mem, "a": a, "d": d, "ops": [], "cost": 0}


def sim(st, seq):
    mem = st["mem"]
    for ch in seq:
        d = st["d"]
        if ch == CH_DLD:
            st["d"] = mem[d]
        elif ch == CH_ROT:
            mem[d] = rot_op(mem[d])
            st["a"] = mem[d]
        elif ch == CH_CRZ:
            mem[d] = crazy_op(st["a"], mem[d])
            st["a"] = mem[d]
        st["d"] = (st["d"] + 1) % MEM_SIZE
    st["ops"].append(seq)
    st["cost"] += len(seq)


def clone(st):
    return {"mem": st["mem"].copy(), "a": st["a"], "d": st["d"],
            "ops": st["ops"] + [""], "cost": st["cost"]}


def return_to_82_from(addr, mem_arr):
    if addr >= 59047:
        return CH_NOP * (59049 - addr) + CH_DLD + CH_NOP
    r = addr + 1
    while r < 59049 and mem_arr[r] != 81:
        r += 1
    if r < 59049:
        return CH_NOP * (r - addr - 1) + CH_DLD
    return CH_NOP * (59049 - addr) + CH_DLD + CH_NOP


def build_write_candidates(st, addr, targ_v, base_dest, high_mods, n, beam):
    """Replicate best_write_seq_for_addr. Returns a list of full sequences:
    one for the free/zero/greedy path, six in beam mode."""
    mem, a = st["mem"], st["a"]
    curr_val = mem[addr]
    offset = addr - base_dest
    ret_ops = return_to_82_from(addr, mem)
    prefix = ""
    a_pre = a
    if CS.find_a_for_crazy(curr_val, targ_v) is None:
        prefix = CH_ROT + CH_DLD + CH_DLD + CH_NOP * (offset - 1) + CH_CRZ + ret_ops
        curr_val = C29524
        a_pre = C29524
    a_req = CS.find_a_for_crazy(curr_val, targ_v)
    assert a_req is not None, (addr, targ_v)
    tail = CH_NOP * (offset - 1) + CH_CRZ + ret_ops
    if a_pre == a_req:
        return [prefix + CH_NOP + CH_DLD + CH_DLD + tail]
    if a_req == 0:
        return [prefix + CH_ROT + CH_DLD + CH_DLD + tail]

    def cand_seqs():
        for sp, nop_entry, z_entry in ALL_SPS:
            s1 = nop_entry + CS.solve_sp(a_pre, mem[sp + 2], mem[sp + 3], a_req)
            s2 = z_entry + CS.solve_sp(0, mem[sp + 2], mem[sp + 3], a_req)
            yield sp, s1, s2

    if not beam:
        orig_v = high_mods[addr]
        if LIN_END < orig_v < n:
            home = 33
        elif orig_v < 2000 or orig_v == 29443:
            home = 48
        else:
            home = 71
        best, best_score = None, 10 ** 9
        for sp, s1, s2 in cand_seqs():
            cand = s1 if len(s1) <= len(s2) else s2
            pen = 0 if (sp == home or mem[sp + 3] == a_req) else 1
            if len(cand) + pen < best_score:
                best_score = len(cand) + pen
                best = cand
        return [prefix + best + CH_DLD + tail]
    out = []
    for _sp, s1, s2 in cand_seqs():
        out.append(prefix + s1 + CH_DLD + tail)
        out.append(prefix + s2 + CH_DLD + tail)
    return out


def set_dest(st, new_dest):
    mem = st["mem"]
    curr_94 = mem[94]
    if curr_94 == new_dest:
        return "noop"
    if new_dest == curr_94 + 9:
        old_94 = mem[94]
        for k_cell in (92, 91, 90, 89):
            m88 = crazy_op(C29524, mem[88])
            v1 = crazy_op(C59048, old_94)
            m88_2 = crazy_op(v1, m88)
            mk = crazy_op(m88_2, mem[k_cell])
            if crazy_op(mk, v1) == new_dest:
                mid = [CH_NOP] * 4
                mid[k_cell - 89] = CH_CRZ
                seq = (CH_NOP * 5 + CH_ROT + CH_CRZ + CH_NOP * 4 + CH_ROT + CH_CRZ
                       + CH_DLD + CH_CRZ + "".join(mid) + CH_NOP + CH_CRZ
                       + CH_NOP + CH_DLD)
                sim(st, seq)
                assert st["d"] == 82 and mem[94] == new_dest
                return "plus9"
    a_req = CS.find_a_for_crazy(curr_94, new_dest)
    if a_req is None:
        sim(st, RESET_94_SEQ)
        assert st["d"] == 82 and mem[94] == C29524
        curr_94 = C29524
        a_req = CS.find_a_for_crazy(curr_94, new_dest)
        assert a_req is not None
        reset = True
    else:
        reset = False
    sp_ops = CS.solve_sp(st["a"], mem[73], mem[74], a_req)
    sim(st, CH_NOP * 3 + CH_DLD + sp_ops + CH_CRZ + CH_NOP + CH_DLD)
    assert st["d"] == 82 and mem[94] == new_dest
    return "sd94+reset" if reset else "sd94"


def do_sweep(st, base_dest, to_flip):
    parts = [CH_ROT, CH_DLD, CH_DLD]
    cur = base_dest + 1
    for addr in to_flip:
        parts.append(CH_NOP * (addr - cur))
        parts.append(CH_CRZ)
        cur = addr + 1
    sim(st, "".join(parts))
    ret_s = return_to_82_from(to_flip[-1], st["mem"])
    sim(st, ret_s)
    assert st["d"] == 82


def do_final94(st, target_94, handoff_d):
    mem = st["mem"]
    curr_94 = mem[94]
    a_req = CS.find_a_for_crazy(curr_94, target_94)
    if a_req is None:
        sim(st, RESET_94_SEQ)
        assert st["d"] == 82 and mem[94] == C29524
        curr_94 = C29524
        a_req = CS.find_a_for_crazy(curr_94, target_94)
        assert a_req is not None
        reset = True
    else:
        reset = False
    sp_ops = CS.solve_sp(st["a"], mem[73], mem[74], a_req)
    sim(st, CH_NOP * 3 + CH_DLD + sp_ops + CH_CRZ + CH_DLD + CH_NOP * 6 + CH_DLD)
    assert st["d"] == handoff_d
    return reset


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--beam", type=int, default=0, help="0 = greedy control; N = beam width")
    ap.add_argument("--demand", type=Path, default=HERE / "out_demand.json")
    ap.add_argument("--out", type=Path, default=HERE / "out_beam_ops.txt")
    ap.add_argument("--need", type=int, default=5883,
                    help="write-phase op ceiling for the target k (default k=19)")
    args = ap.parse_args()
    beam_mode = args.beam > 0
    beam_w = args.beam

    clean, high_mods, handoff_d, _hct = CS.extract_target_state(REF, LIN_END)
    n = len(clean)
    template_clean = [b for b in REF.read_bytes() if 33 <= b <= 126]
    boot_ops, boot_mem, boot_a, boot_d = build_compact_boot(
        rebuild_orig_boot_ops(template_clean, n), template_clean, high_mods)
    assert boot_d == 82 and len(boot_ops) == 1235

    rows = json.loads(args.demand.read_text())
    print(f"mode: {'beam ' + str(beam_w) if beam_mode else 'greedy control (validation)'}")
    print(f"boot 1,235 ops; rows {len(rows)}; handoff_d {handoff_d}")

    states = [new_state(boot_mem.copy(), boot_a, boot_d)]
    checks = {"write_len_ok": 0, "write_len_bad": 0, "plus9_ok": 0,
              "sweep_ok": 0, "sd94_ok": 0, "final_ok": 0}
    for i, row in enumerate(rows):
        kind = row[0]
        nxt = []
        if kind == "write":
            addr, targ_v, base = row[1], row[2], row[7]
            for st in states:
                assert st["mem"][94] == base, (i, st["mem"][94], base)
                cands = build_write_candidates(st, addr, targ_v, base, high_mods, n, beam_mode)
                for seq in cands:
                    ns = clone(st)
                    ns["ops"][-1] = seq
                    # simulate on the clone
                    for ch in seq:
                        d = ns["d"]
                        if ch == CH_DLD:
                            ns["d"] = ns["mem"][d]
                        elif ch == CH_ROT:
                            ns["mem"][d] = rot_op(ns["mem"][d])
                            ns["a"] = ns["mem"][d]
                        elif ch == CH_CRZ:
                            ns["mem"][d] = crazy_op(ns["a"], ns["mem"][d])
                            ns["a"] = ns["mem"][d]
                        ns["d"] = (ns["d"] + 1) % MEM_SIZE
                    ns["cost"] += len(seq)
                    assert ns["d"] == 82 and ns["mem"][addr] == targ_v
                    nxt.append(ns)
                if not beam_mode:
                    assert len(cands) == 1
                    if len(cands[0]) == row[6]:
                        checks["write_len_ok"] += 1
                    else:
                        checks["write_len_bad"] += 1
                        print(f"  write len mismatch row {i}: {len(cands[0])} != {row[6]}")
        elif kind in ("plus9", "sd94"):
            for st in states:
                path = set_dest(st, row[2])
                if not beam_mode:
                    expect = {"plus9": ("plus9",), "sd94": ("sd94", "sd94+reset")}[kind]
                    assert path in expect, (i, path, kind)
                    if kind == "plus9" and len(st["ops"][-1]) == row[6]:
                        checks["plus9_ok"] += 1
                    if kind == "sd94":
                        checks["sd94_ok"] += 1
            nxt = states
        elif kind == "reset94":
            nxt = states  # internal to the following set_dest/final94 call
        elif kind == "sweep":
            for st in states:
                before = st["cost"]
                do_sweep(st, row[1], row[2])
                if not beam_mode:
                    if st["cost"] - before == row[6]:
                        checks["sweep_ok"] += 1
            nxt = states
        elif kind == "final94":
            for st in states:
                reset = do_final94(st, row[2], handoff_d)
                if not beam_mode:
                    checks["final_ok"] += 1
            nxt = states
        else:
            raise ValueError(kind)

        if beam_mode and kind == "write":
            dedup = {}
            for st in nxt:
                key = (tuple(st["mem"][30:100]), st["a"])
                if key not in dedup or st["cost"] < dedup[key]["cost"]:
                    dedup[key] = st
            nxt = sorted(dedup.values(), key=lambda s: s["cost"])[:beam_w]
        states = nxt
        if (i + 1) % 25 == 0:
            best = min(s["cost"] for s in states)
            print(f"  row {i + 1}/{len(rows)}: {len(states)} states, best {best}")

    best = min(states, key=lambda s: s["cost"])
    print(f"== write-phase replay total: {best['cost']} ops "
          f"(+1 JMP = {best['cost'] + 1})")
    if not beam_mode:
        expected = sum(r[6] + (3 if r[0] == "sd94" else 9 if r[0] == "final94" else 0)
                       for r in rows)
        print(f"== control checks: {checks}")
        assert best["cost"] == expected, f"control failed: {best['cost']} != {expected}"
        assert checks["write_len_bad"] == 0
        print(f"== CONTROL PASS: replay is faithful ({expected} + JMP)")
    else:
        out = "".join(best["ops"])
        args.out.write_text(out)
        print(f"== beam best: {best['cost']}  (need <= {args.need}; "
          f"gain vs greedy {sum(r[6] for r in rows) and (sum(r[6] + (3 if r[0]=='sd94' else 9 if r[0]=='final94' else 0) for r in rows) - best['cost'])})")
        print(f"   op stream written: {args.out} ({len(out)} chars)")


if __name__ == "__main__":
    main()
