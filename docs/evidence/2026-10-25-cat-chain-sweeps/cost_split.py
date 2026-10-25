"""Cost split of the k=18 Cat preamble: arithmetic (solve_sp) vs d-movement.

Motivated by the m1 limits work (`*jo` stationary register) and by the question
"can a d-anchoring gadget close the 118-operation gap?".  The published
`chain_synth.py` is used unchanged except for four bookkeeping hooks that record,
per write, how many of its operations are

    arith : the `solve_sp` string itself (the search that lands `a` on a_req)
    move  : the entry pad into the spindle + final DLD (d positioning)
    walk  : the NOP offset walk from the window base to the target
    ret   : return_to_82_from(target)

Run: python3 docs/evidence/2026-10-25-cat-chain-sweeps/cost_split.py
"""
from __future__ import annotations

import importlib.util
import random
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

SRC = HERE / "chain_synth.py"
PATCHES = [
    (
        "    WRITE_TRACE: list[tuple[int, int, int, int, int]] = []",
        "    WRITE_TRACE: list[tuple[int, int, int, int, int]] = []\n"
        "    WRITE_COMP.clear()\n"
        "    LAST_COMP_BY_ADDR.clear()",
    ),
    (
        "def synthesize_preamble_ops(",
        "WRITE_COMP: list[dict] = []\n"
        "BOOT_TRACE: list = []\n"
        "LAST_COMP_BY_ADDR: dict = {}\n"
        "ARITH = [0]\n\n"
        "def synthesize_preamble_ops(",
    ),
    (
        "    def best_write_seq_for_addr(addr: int, base_dest: int, target_val: int) -> str:\n"
        "        curr_val = mem[addr]",
        "    def best_write_seq_for_addr(addr: int, base_dest: int, target_val: int) -> str:\n"
        "        ARITH[0] = 0\n"
        "        curr_val = mem[addr]",
    ),
    (
        "                cand = s1 if len(s1) <= len(s2) else s2",
        "                cand = s1 if len(s1) <= len(s2) else s2\n"
        "                cand_move = len(nop_entry) if cand is s1 else len(z_entry)",
    ),
    (
        "                if len(cand) + borrow_pen < best_sp_score:\n"
        "                    best_sp_score = len(cand) + borrow_pen\n"
        "                    best_sp = cand",
        "                if len(cand) + borrow_pen < best_sp_score:\n"
        "                    best_sp_score = len(cand) + borrow_pen\n"
        "                    best_sp = cand\n"
        "                    ARITH[0] = len(cand) - cand_move",
    ),
    (
        "        return prefix_preclear + compute_and_jump + CH_NOP * (offset - 1) + CH_CRZ + ret_ops",
        "        total = prefix_preclear + compute_and_jump + CH_NOP * (offset - 1) + CH_CRZ + ret_ops\n"
        "        LAST_COMP_BY_ADDR[addr] = dict(\n"
        "            addr=addr, targ=target_val, a_req=a_req, a_in=a,\n"
        "            pre=len(prefix_preclear), arith=ARITH[0],\n"
        "            move=len(compute_and_jump) - ARITH[0],\n"
        "            walk=offset - 1, ret=len(ret_ops), total=len(total))\n"
        "        return total",
    ),
    (
        "                WRITE_TRACE.append((addr, targ_v, a, len(best_seq), mem[addr]))",
        "                WRITE_TRACE.append((addr, targ_v, a, len(best_seq), mem[addr]))\n"
        "                WRITE_COMP.append(dict(LAST_COMP_BY_ADDR[addr]))",
    ),
    (
        "            seq = solve_sp(a, mem[sp_b + 2], mem[sp_b + 3], targ_a)\n"
        "            sim_ops(seq)\n"
        "            b_idx = end_idx + 1",
        "            seq = solve_sp(a, mem[sp_b + 2], mem[sp_b + 3], targ_a)\n"
        "            BOOT_TRACE.append(('solve', b_idx, len(seq)))\n"
        "            sim_ops(seq)\n"
        "            b_idx = end_idx + 1",
    ),
    (
        "        else:\n"
        "            sim_ops(orig_boot_ops[b_idx])\n"
        "            b_idx += 1",
        "        else:\n"
        "            BOOT_TRACE.append(('literal', b_idx, len(orig_boot_ops[b_idx])))\n"
        "            sim_ops(orig_boot_ops[b_idx])\n"
        "            b_idx += 1",
    ),
]


def load_probe():
    src = SRC.read_text()
    root_line = "REPO_ROOT = Path(__file__).resolve().parents[2]"
    if root_line not in src:
        raise SystemExit("chain_synth.py changed; REPO_ROOT line not found")
    src = src.replace(root_line, f"REPO_ROOT = Path({str(ROOT)!r})", 1)
    for old, new in PATCHES:
        if old not in src:
            raise SystemExit("chain_synth.py changed; hook not found:\n" + old[:80])
        src = src.replace(old, new, 1)
    tmp = Path(tempfile.mkdtemp(prefix="cat_cost_")) / "chain_cost.py"
    tmp.write_text(src)
    spec = importlib.util.spec_from_file_location("chain_cost", tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    C = load_probe()
    ref = ROOT / "reference" / "malbolge_org" / "cat.mal"
    clean, high, hd, _ = C.extract_target_state(ref, 9003)
    template = [b for b in ref.read_bytes() if 33 <= b <= 126]

    ops = C.synthesize_preamble_ops(
        clean, high, hd, 9003, delta=94 * 18, template_clean=template,
        borrow_penalty=1, direct_gap=18, rng=random.Random(9803),
        restart_p1=0.80, restart_p2=0.90)

    last: dict[int, dict] = {}
    for row in C.WRITE_COMP:
        last[row["addr"]] = row
    rows = sorted(last.values(), key=lambda r: r["addr"])
    keys = ["pre", "arith", "move", "walk", "ret", "total"]
    sums = {k: sum(r[k] for r in rows) for k in keys}

    print(f"plan seed 9803          : {len(ops)} ops (budget 7213)")
    print(f"writes traced           : {len(rows)}")
    for k in keys:
        print(f"  {k:6s} {sums[k]:6d}  ({100 * sums[k] / sums['total']:5.1f}% of writes)")
    print(f"  d-movement (move+walk+ret) {sums['move'] + sums['walk'] + sums['ret']}")
    print(f"  outside the 121 writes  : {len(ops) - sums['total']}")
    boot = C.BOOT_TRACE
    b_solve = [r for r in boot if r[0] == "solve"]
    b_lit = [r for r in boot if r[0] == "literal"]
    print(f"    boot solves           : {len(b_solve):3d} calls, {sum(r[2] for r in b_solve)} ops")
    print(f"    boot literal ops      : {len(b_lit):3d} cells, {sum(r[2] for r in b_lit)} ops")
    print(f"    boot total            : {sum(r[2] for r in boot)} ops")

    heavy = [r for r in rows if r["arith"] >= 25]
    print(f"  writes with arith>=25   : {len(heavy)} (sum arith {sum(r['arith'] for r in heavy)})")

    a_req = [r["a_req"] for r in rows]
    counts: dict[int, int] = {}
    for x in a_req:
        counts[x] = counts.get(x, 0) + 1
    repeated = {x: n for x, n in counts.items() if n > 1}
    print(f"  distinct a_req          : {len(counts)}/{len(a_req)}"
          f"  (repeated values cover {sum(repeated.values())} writes)")
    print(f"  top repeats             : "
          + ", ".join(f"{x}x{n}" for x, n in sorted(repeated.items(), key=lambda kv: -kv[1])[:5]))

    rot = lambda x: (x // 3) + (x % 3) * 19683  # noqa: E731
    same = sum(1 for i in range(len(a_req) - 1) if a_req[i] == a_req[i + 1])
    rot1 = sum(1 for i in range(len(a_req) - 1) if a_req[i + 1] == rot(a_req[i]))
    print(f"  consecutive a_req       : same {same}, rot {rot1}, other {len(a_req) - 1 - same - rot1}")


if __name__ == "__main__":
    main()
