"""Joint search: write ORDER x spindle/entry ASSIGNMENT, per window.

The demand file fixes the window structure (base advances, sweeps, sd94,
final94 — all replayed as invariant rows) and the set of writes per window.
Inside each window the recorded plan commits to one order chosen by the
seeded greedy; this search keeps a beam over (memory, a, remaining-writes)
states and chooses, per state, WHICH remaining target to write next and with
WHICH (spindle, entry) candidate — the two levers optimized jointly on the
real machine state (no cost model).

Control: --fixed-order replays the recorded order with the same beam — at
width 512 it must reproduce w2's beam result on the same demand (5,991 ops).

Run:
  python3 docs/evidence/2026-10-25-cat-k19-frontier/w3_joint.py --beam 512 --fixed-order   # control
  python3 docs/evidence/2026-10-25-cat-k19-frontier/w3_joint.py --beam 128                   # joint
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from constants import MEM_SIZE, crazy_op, rot_op  # noqa: E402
from tools.compact_boot import (  # noqa: E402
    build_compact_boot, rebuild_orig_boot_ops,
)
from tools.resynthesize import extract_target_state  # noqa: E402
from w2_beam import (  # noqa: E402
    build_write_candidates, clone, do_final94, do_sweep, new_state, set_dest,
)

REF = ROOT / "reference" / "malbolge_org" / "cat.mal"


def sim_on(st, seq):
    mem = st["mem"]
    for ch in seq:
        d = st["d"]
        if ch == "j":
            st["d"] = mem[d]
        elif ch == "*":
            mem[d] = rot_op(mem[d])
            st["a"] = mem[d]
        elif ch == "p":
            mem[d] = crazy_op(st["a"], mem[d])
            st["a"] = mem[d]
        st["d"] = (st["d"] + 1) % MEM_SIZE
    st["ops"][-1] = seq
    st["cost"] += len(seq)


def flush_window(states, writes, beam_w, fixed_order, high_mods, n):
    for st in states:
        st["rem"] = frozenset(range(len(writes)))
    for step in range(len(writes)):
        nxt: dict = {}
        for st in states:
            choices = [step] if fixed_order else sorted(st["rem"])
            for wi in choices:
                addr, targ_v, base = writes[wi]
                assert st["mem"][94] == base
                cands = build_write_candidates(
                    st, addr, targ_v, base, high_mods, n, beam=True)
                for seq in cands:
                    ns = clone(st)
                    ns["rem"] = st["rem"] - {wi}
                    sim_on(ns, seq)
                    assert ns["d"] == 82 and ns["mem"][addr] == targ_v
                    key = (tuple(ns["mem"][30:100]), ns["a"], ns["rem"])
                    cur = nxt.get(key)
                    if cur is None or ns["cost"] < cur["cost"]:
                        nxt[key] = ns
        states = sorted(nxt.values(), key=lambda s: s["cost"])[:beam_w]
        if not states:
            raise SystemExit("beam collapsed in window")
    for st in states:
        assert not st["rem"]
        del st["rem"]
    return states


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--beam", type=int, default=128)
    ap.add_argument("--demand", type=Path,
                    default=HERE / "out_demand_k19s9330.json")
    ap.add_argument("--fixed-order", action="store_true")
    ap.add_argument("--out", type=Path, default=HERE / "out_joint_ops.txt")
    args = ap.parse_args()

    clean, high_mods, handoff_d, _ = extract_target_state(REF, 9003)
    template = [b for b in REF.read_bytes() if 33 <= b <= 126]
    n = len(clean)
    obo = rebuild_orig_boot_ops(template, n)
    boot_ops, boot_mem, boot_a, boot_d = build_compact_boot(
        obo, template, high_mods)
    assert boot_d == 82 and len(boot_ops) == 1235

    rows = json.loads(args.demand.read_text())
    mode = "fixed-order" if args.fixed_order else "JOINT"
    print(f"== w3 {mode}, beam {args.beam} ==")

    states = [new_state(boot_mem.copy(), boot_a, boot_d)]
    buffer: list = []
    windows = 0
    for row in rows:
        kind = row[0]
        if kind == "write":
            buffer.append((row[1], row[2], row[7]))
            continue
        if buffer:
            states = flush_window(states, buffer, args.beam,
                                  args.fixed_order, high_mods, n)
            windows += 1
            buffer = []
        if kind in ("plus9", "sd94"):
            for st in states:
                set_dest(st, row[2])
        elif kind == "reset94":
            pass
        elif kind == "sweep":
            for st in states:
                do_sweep(st, row[1], row[2])
        elif kind == "final94":
            for st in states:
                do_final94(st, row[2], handoff_d)
    if buffer:
        states = flush_window(states, buffer, args.beam,
                              args.fixed_order, high_mods, n)
        windows += 1

    best = min(states, key=lambda s: s["cost"])
    out = "".join(best["ops"])
    print(f"windows: {windows}; best write phase: {best['cost']} ops "
          f"(recorded beam-512 at fixed order: 5991)")
    print(f"k=19 total with boot 1,177 + JMP: {1177 + best['cost'] + 1} "
          f"(budget 7,119)")
    args.out.write_text(out)
    print(f"op stream written -> {args.out} ({len(out)} chars)")


if __name__ == "__main__":
    main()
