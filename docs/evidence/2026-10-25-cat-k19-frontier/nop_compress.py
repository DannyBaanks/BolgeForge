"""NOP-run compression: skip d-walks with j-jumps over frozen cells.

A maximal run of NOP ops advances d one cell per op and writes nothing, so
the memory is frozen for the whole run. Any cell x on the run whose value v
satisfies (v + 1) being a later position inside the same run can replace the
whole skipped stretch with a single `j` (d = mem[d]; d advances by 1 per op).
Replacing a NOP-run by the shortest walk/jump chain leaves the (a, d, mem)
state at the run's end IDENTICAL — no liveness analysis needed, no risk to
any downstream op.

This pass applies to any plan (boot or write phase). It never lengthens a
run, never touches non-NOP ops, and the equivalence is asserted: every
non-NOP op of the compressed plan must observe the same (a, d) as the
original, and the final memory must be byte-identical.

Why it matters: the k=19 budget needs -108 ops. The compact boot alone has
687 NOP ops (55%) with runs up to 18; the best k=19 write stream (5,991 ops)
carries the offset walks and return walks of 121 writes.

Run:
  python3 docs/evidence/2026-10-25-cat-k19-frontier/nop_compress.py \
      --ops-file out_beam_k19s9330_ops.txt --boot   # k19 full plan
  python3 docs/evidence/2026-10-25-cat-k19-frontier/nop_compress.py \
      --plan k18                                     # canonical k18 plan
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import deque
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


def sim_state(plan, mem, a=0, d=1):
    """Simulate; yield (a, d) before each op; return final (a, d)."""
    for ch in plan:
        yield a, d
        if ch == CH_DLD:
            d = mem[d]
        elif ch == CH_ROT:
            mem[d] = rot_op(mem[d])
            a = mem[d]
        elif ch == CH_CRZ:
            mem[d] = crazy_op(a, mem[d])
            a = mem[d]
        d = (d + 1) % MEM_SIZE
    yield a, d


def compress(plan: str, mem0: list[int]):
    """Return (compressed_plan, stats). mem0 is the fill state (copied)."""
    mem = list(mem0)
    a, d = 0, 1
    out = []
    mapping = []
    stats = {"runs": 0, "runs_shortened": 0, "ops_before": len(plan),
             "ops_saved": 0, "longest_run": 0}
    i = 0
    n = len(plan)
    while i < n:
        ch = plan[i]
        if ch != CH_NOP:
            # apply and advance (state evolves exactly like the original)
            if ch == CH_DLD:
                d = mem[d]
            elif ch == CH_ROT:
                mem[d] = rot_op(mem[d])
                a = mem[d]
            elif ch == CH_CRZ:
                mem[d] = crazy_op(a, mem[d])
                a = mem[d]
            out.append(ch)
            mapping.append(i)
            d = (d + 1) % MEM_SIZE
            i += 1
            continue
        # maximal NOP run: positions i..j
        j = i
        while j < n and plan[j] == CH_NOP:
            j += 1
        run_len = j - i
        stats["runs"] += 1
        stats["longest_run"] = max(stats["longest_run"], run_len)
        # d sequence of the run: d0, d0+1, ..., d0+run_len (mod MEM_SIZE)
        seq = [(d + k) % MEM_SIZE for k in range(run_len + 1)]
        idx_of = {pos: k for k, pos in enumerate(seq)}
        # shortest chain: BFS over run positions with walk/jump edges
        best = None
        if run_len >= 2:
            dist = {0: 0}
            parent = {}
            q = deque([0])
            while q:
                k = q.popleft()
                if k == run_len:
                    break
                x = seq[k]
                edges = [(k + 1, False)]
                tgt = (mem[x] + 1) % MEM_SIZE
                m = idx_of.get(tgt)
                if m is not None and m > k + 1:
                    edges.append((m, True))
                for m2, is_jump in edges:
                    if m2 not in dist:
                        dist[m2] = dist[k] + 1
                        parent[m2] = (k, is_jump)
                        q.append(m2)
            if run_len in dist and dist[run_len] < run_len:
                chain = []
                k = run_len
                while k != 0:
                    pk, is_jump = parent[k]
                    chain.append(CH_DLD if is_jump else CH_NOP)
                    k = pk
                chain.reverse()
                best = chain
        if best is not None:
            out.extend(best)
            mapping.extend([-1] * len(best))
            stats["runs_shortened"] += 1
            stats["ops_saved"] += run_len - len(best)
        else:
            out.extend(CH_NOP * run_len)
            mapping.extend(range(i, j))
        # no writes happen inside a NOP run: state frozen, d lands at the end
        d = seq[run_len] if run_len else d
        i = j
    stats["ops_after"] = len(out)
    return "".join(out), mapping, stats


def verify_equivalence(orig: str, comp: str, mapping: list[int], mem0: list[int]):
    """Assert: every compressed op that maps to an original op sees the exact
    original (a, d) and is the same op; chain ops are simulated freely; the
    final memory must be identical."""
    # original states before each op
    mem_o = list(mem0)
    orig_states = []
    a, d = 0, 1
    for ch in orig:
        orig_states.append((a, d))
        if ch == CH_DLD:
            d = mem_o[d]
        elif ch == CH_ROT:
            mem_o[d] = rot_op(mem_o[d])
            a = mem_o[d]
        elif ch == CH_CRZ:
            mem_o[d] = crazy_op(a, mem_o[d])
            a = mem_o[d]
        d = (d + 1) % MEM_SIZE
    orig_states.append((a, d))
    # simulate compressed, checking mapped boundaries
    mem_c = list(mem0)
    a, d = 0, 1
    checked = 0
    for t, ch in enumerate(comp):
        oi = mapping[t]
        if oi >= 0:
            assert (a, d) == orig_states[oi], (t, oi, a, d, orig_states[oi])
            assert ch == orig[oi]
            checked += 1
        if ch == CH_DLD:
            d = mem_c[d]
        elif ch == CH_ROT:
            mem_c[d] = rot_op(mem_c[d])
            a = mem_c[d]
        elif ch == CH_CRZ:
            mem_c[d] = crazy_op(a, mem_c[d])
            a = mem_c[d]
        d = (d + 1) % MEM_SIZE
    assert (a, d) == orig_states[len(orig)], "final (a, d) differs"
    assert mem_c == mem_o, "final memory differs"
    return checked


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", choices=["k18"], default=None)
    ap.add_argument("--ops-file", type=Path, default=None,
                    help="write-phase op stream (k19 beam output)")
    ap.add_argument("--boot", action="store_true", help="prepend the compact boot")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    clean, high_mods, hd, _ = extract_target_state(REF, 9003)
    template = [b for b in REF.read_bytes() if 33 <= b <= 126]
    n = len(clean)
    mem0 = planner_fill_mem(template, n)

    if args.plan == "k18":
        plan_ops = synthesize_preamble_ops(
            clean, high_mods, hd, 9003, delta=94 * 18, template_clean=template,
            borrow_penalty=1, direct_gap=18, rng=random.Random(9803),
            restart_p1=0.80, restart_p2=0.90, boot="compact")
        plan = "".join(plan_ops)
        label = "k18 full plan"
    else:
        assert args.ops_file is not None
        parts = []
        if args.boot:
            obo = rebuild_orig_boot_ops(template, n)
            boot_ops, _m, _a, _d = build_compact_boot(obo, template, high_mods)
            parts.append("".join(boot_ops))
        parts.append(args.ops_file.read_text().strip())
        plan = "".join(parts)
        label = f"boot+{args.ops_file.name}" if args.boot else args.ops_file.name

    comp, mapping, stats = compress(plan, mem0)
    checked = verify_equivalence(plan, comp, mapping, mem0)
    print(f"== {label} ==")
    for k, v in stats.items():
        print(f"  {k:16s} {v}")
    print(f"  boundary checks   {checked}")
    print(f"  compressed length {len(comp)}")
    if args.out:
        args.out.write_text(comp)
        print(f"  written -> {args.out}")


if __name__ == "__main__":
    main()
