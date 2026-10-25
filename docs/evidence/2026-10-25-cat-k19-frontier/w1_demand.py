"""k=19 frontier probe: the three spindles as an a_req cache.

Hypothesis H: each ``solve_sp`` call ends with the tracked spindle cell holding
the ``a_req`` it just produced, so the three spindles (33/48/71) act as a
3-slot cache of recent ``a_req`` values. The planner chooses greedily (min
length today); an assignment keeping the most-demanded values cached could
cut the write phase by >= 80 ops — exactly what k=19 needs
(boot 1,235 + write <= 7,119 -> write <= 5,884; current write 5,964).

H0 (null): on the same demand sequence the greedy spindle choice is within
80 ops of the best possible assignment.

Method: instrument the k=18 seed-9803 plan (write phase is k-invariant),
extract the demand sequence in execution order with each row's ``a_req``
computed at choice time, verify the cache property directly
(``x_in`` of each demand on spindle s == ``a_req`` of the previous demand on
s), then bound the policy gain with a beam search over cache states under a
z-entry cost model  c_s(v,w) = entry_len(s) + len(solve_sp(0, temp_s, v, w)).

Run: python3 docs/evidence/2026-10-25-cat-k19-frontier/w1_demand.py
"""
from __future__ import annotations

import random
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

import chain_synth as CS  # noqa: E402
from tools.compact_boot import build_compact_boot  # noqa: E402
from verify_k18 import BOOT_BLOCK  # noqa: E402

REF = ROOT / "reference" / "malbolge_org" / "cat.mal"
DELTA = 94 * 18
SEED = 9803
INF = 10 ** 9

ROW_CTX_INIT = (
    'ROW_CTX = {"buf": [], "win": [], "main": [], "meta": {}, "last": None,'
    ' "seq": [], "consumed": 0, "combo": 0, "simlens": []}\n\n'
    "def synthesize_preamble_ops("
)
NEW_BOOT = """    ops_b, mem_b, a_b, d_b = _CUSTOM_BOOT(orig_boot_ops, template_clean, high_mods, first_base_at_min)
    ops_out.extend(ops_b)
    mem[:] = mem_b
    a, d = a_b, d_b
    assert d == 82"""

PATCHES = [
    (
        "    def run_window_strategy(window: list[tuple[int, int]], use_domino: bool, respect_81: bool) -> str:\n"
        "        nonlocal a, d",
        "    def run_window_strategy(window: list[tuple[int, int]], use_domino: bool, respect_81: bool) -> str:\n"
        "        nonlocal a, d\n"
        "        ROW_CTX['combo'] += 1\n"
        "        ROW_CTX['buf'] = []",
    ),
    (
        "            best_sp = None\n            best_sp_score = 10**9\n",
        "            best_sp = None\n            best_sp_score = 10**9\n            best_meta = None\n",
    ),
    (
        "                if len(cand) + borrow_pen < best_sp_score:\n"
        "                    best_sp_score = len(cand) + borrow_pen\n"
        "                    best_sp = cand\n"
        "            assert best_sp is not None\n"
        "            compute_and_jump = best_sp + CH_DLD",
        "                if len(cand) + borrow_pen < best_sp_score:\n"
        "                    best_sp_score = len(cand) + borrow_pen\n"
        "                    best_sp = cand\n"
        "                    entry_len = len(nop_entry) if cand is s1 else len(z_entry)\n"
        "                    best_meta = ('live' if cand is s1 else 'zero', sp_base,\n"
        "                                entry_len, len(cand) - entry_len,\n"
        "                                mem[sp_base + 3], mem[sp_base + 2], a_after_pre)\n"
        "            assert best_sp is not None\n"
        "            compute_and_jump = best_sp + CH_DLD",
    ),
    (
        "        if a_after_pre == a_req:\n"
        "            compute_and_jump = CH_NOP + CH_DLD + CH_DLD\n"
        "        elif a_req == 0:\n"
        "            compute_and_jump = CH_ROT + CH_DLD + CH_DLD\n",
        "        if a_after_pre == a_req:\n"
        "            compute_and_jump = CH_NOP + CH_DLD + CH_DLD\n"
        "            best_meta = ('free', None, 0, 0, None, None, a_after_pre)\n"
        "        elif a_req == 0:\n"
        "            compute_and_jump = CH_ROT + CH_DLD + CH_DLD\n"
        "            best_meta = ('zero', None, 0, 0, None, None, 0)\n",
    ),
    (
        "        return prefix_preclear + compute_and_jump + CH_NOP * (offset - 1) + CH_CRZ + ret_ops",
        "        ROW_CTX['last'] = best_meta\n"
        "        return prefix_preclear + compute_and_jump + CH_NOP * (offset - 1) + CH_CRZ + ret_ops",
    ),
    (
        "                for i_rem, (addr, targ_v) in enumerate(remaining):\n"
        "                    seq = best_write_seq_for_addr(addr, base_dest, targ_v)\n"
        "                    penalty = 0",
        "                for i_rem, (addr, targ_v) in enumerate(remaining):\n"
        "                    seq = best_write_seq_for_addr(addr, base_dest, targ_v)\n"
        "                    ROW_CTX['meta'][i_rem] = (targ_v, ROW_CTX['last'])\n"
        "                    penalty = 0",
    ),
    (
        "                WRITE_TRACE.append((addr, targ_v, a, len(best_seq), mem[addr]))",
        "                WRITE_TRACE.append((addr, targ_v, a, len(best_seq), mem[addr]))\n"
        "                _tv, _m = ROW_CTX['meta'].get(best_i, (targ_v, None))\n"
        "                _ar = find_a_for_crazy(mem[addr], targ_v)\n"
        "                _pre = False\n"
        "                if _ar is None:\n"
        "                    _ar = find_a_for_crazy(C29524, targ_v)\n"
        "                    _pre = True\n"
        "                ROW_CTX['buf'].append(('write', addr, targ_v, _ar, _pre, _m, len(best_seq), base_dest))",
    ),
    (
        "                    if best_w9 is None or len(cand_w) < len(best_w9):\n"
        "                        best_w9 = cand_w",
        "                    if best_w9 is None or len(cand_w) < len(best_w9):\n"
        "                        best_w9 = cand_w\n"
        "                        ROW_CTX['win'] = list(ROW_CTX['buf'])",
    ),
    (
        "            assert best_w9 is not None\n"
        "            sim_ops(best_w9)\n"
        "            for addr, targ_v in w9:\n"
        "                assert mem[addr] == targ_v\n"
        "        idx = idx9",
        "            assert best_w9 is not None\n"
        "            sim_ops(best_w9)\n"
        "            for addr, targ_v in w9:\n"
        "                assert mem[addr] == targ_v\n"
        "            ROW_CTX['seq'].extend(ROW_CTX['main'][ROW_CTX['consumed']:])\n"
        "            ROW_CTX['consumed'] = len(ROW_CTX['main'])\n"
        "            ROW_CTX['seq'].extend(ROW_CTX['win'])\n"
        "        idx = idx9",
    ),
    (
        "        sp_ops = solve_sp(a, mem[71 + 2], mem[71 + 3], a_req)\n"
        "        sim_ops(CH_NOP * 3 + CH_DLD + sp_ops + CH_CRZ + CH_NOP + CH_DLD)\n"
        "        assert d == 82 and mem[94] == new_dest",
        "        sp_ops = solve_sp(a, mem[71 + 2], mem[71 + 3], a_req)\n"
        "        ROW_CTX['main'].append(('sd94', None, new_dest, a_req, False,\n"
        "            ('live', 71, 4, len(sp_ops), mem[71 + 3], mem[71 + 2], a), len(sp_ops) + 4))\n"
        "        sim_ops(CH_NOP * 3 + CH_DLD + sp_ops + CH_CRZ + CH_NOP + CH_DLD)\n"
        "        assert d == 82 and mem[94] == new_dest",
    ),
    (
        "                    sim_ops(seq)\n"
        "                    assert d == 82 and mem[94] == new_dest\n"
        "                    return",
        "                    sim_ops(seq)\n"
        "                    ROW_CTX['main'].append(('plus9', None, new_dest, 0, False, None, len(seq)))\n"
        "                    assert d == 82 and mem[94] == new_dest\n"
        "                    return",
    ),
    (
        "                    sim_ops(\"\".join(sweep))\n"
        "                    ret_s = return_to_82_from(to_flip[-1], mem)\n"
        "                    sim_ops(ret_s)\n"
        "                    assert d == 82",
        "                    sim_ops(\"\".join(sweep))\n"
        "                    ret_s = return_to_82_from(to_flip[-1], mem)\n"
        "                    sim_ops(ret_s)\n"
        "                    ROW_CTX['buf'].append(('sweep', base_dest, list(to_flip), 0, False, None, len(''.join(sweep)) + len(ret_s)))\n"
        "                    assert d == 82",
    ),
    (
        "        if a_req is None:\n"
        "            sim_ops(RESET_94_SEQ)\n"
        "            assert d == 82 and mem[94] == C29524",
        "        if a_req is None:\n"
        "            sim_ops(RESET_94_SEQ)\n"
        "            ROW_CTX['main'].append(('reset94', None, None, 0, False, None, len(RESET_94_SEQ)))\n"
        "            assert d == 82 and mem[94] == C29524",
    ),
    (
        "    sp_ops = solve_sp(a, mem[71 + 2], mem[71 + 3], a_req)\n"
        "    sim_ops(CH_NOP * 3 + CH_DLD + sp_ops + CH_CRZ + CH_DLD + CH_NOP * 6 + CH_DLD)\n"
        "    assert d == handoff_d",
        "    sp_ops = solve_sp(a, mem[71 + 2], mem[71 + 3], a_req)\n"
        "    ROW_CTX['main'].append(('final94', None, target_94, a_req, False,\n"
        "        ('live', 71, 4, len(sp_ops), mem[71 + 3], mem[71 + 2], a), len(sp_ops) + 4))\n"
        "    sim_ops(CH_NOP * 3 + CH_DLD + sp_ops + CH_CRZ + CH_DLD + CH_NOP * 6 + CH_DLD)\n"
        "    assert d == handoff_d",
    ),
    (
        "    if a_req is None:\n"
        "        sim_ops(RESET_94_SEQ)\n"
        "        curr_94 = C29524",
        "    if a_req is None:\n"
        "        sim_ops(RESET_94_SEQ)\n"
        "        ROW_CTX['main'].append(('reset94', None, None, 0, False, None, len(RESET_94_SEQ)))\n"
        "        curr_94 = C29524",
    ),
    (
        "    def sim_ops(seq: str) -> None:\n"
        "        nonlocal a, d\n"
        "        for ch in seq:\n"
        "            ops_out.append(ch)",
        "    def sim_ops(seq: str) -> None:\n"
        "        nonlocal a, d\n"
        "        ROW_CTX['simlens'].append(len(seq))\n"
        "        for ch in seq:\n"
        "            ops_out.append(ch)",
    ),
]


def load_patched():
    src = (K18 / "chain_synth.py").read_text()
    assert BOOT_BLOCK in src
    src = src.replace(BOOT_BLOCK, NEW_BOOT, 1)
    src = src.replace("def synthesize_preamble_ops(", ROW_CTX_INIT, 1)
    for old, new in PATCHES:
        assert old in src, "missing anchor: " + old[:70]
        src = src.replace(old, new, 1)
    ns = {"__file__": str(K18 / "chain_synth.py"), "_CUSTOM_BOOT": build_compact_boot}
    exec(compile(src, "<chain_synth_w1>", "exec"), ns)
    return ns


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=18)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    delta = 94 * args.k
    clean, high_mods, hd, _ = CS.extract_target_state(REF, 9003)
    template_clean = [b for b in REF.read_bytes() if 33 <= b <= 126]
    ns = load_patched()
    ctx = ns["ROW_CTX"]
    ops = ns["synthesize_preamble_ops"](
        clean, high_mods, hd, 9003, delta=delta, template_clean=template_clean,
        borrow_penalty=1, direct_gap=18, rng=random.Random(args.seed),
        restart_p1=0.80, restart_p2=0.90)
    seq = ctx["seq"] + ctx["main"][ctx["consumed"]:]
    print(f"== control ==  k={args.k} seed={args.seed} total ops {len(ops)}")
    if args.k == 18 and args.seed == 9803:
        assert len(ops) == 7199
    kinds = {}
    for r in seq:
        kinds[r[0]] = kinds.get(r[0], 0) + 1
    print(f"== demand sequence ==  {len(seq)} rows  {kinds}")

    # -- direct cache-property verification ----------------------------------
    init_x: dict[int, int] = {}
    temps: dict[int, set[int]] = {}
    prev_a_req: dict[int, int] = {}
    ok_chain = bad_chain = 0
    for r in seq:
        if r[0] in ("reset94",):
            continue
        kind, a_req, meta = r[0], r[3], r[5]
        if meta is None or meta[1] is None:
            continue
        branch, sp = meta[0], meta[1]
        x_in, temp_in = meta[4], meta[5]
        if sp not in init_x:
            init_x[sp] = x_in
        temps.setdefault(sp, set()).add(temp_in)
        if branch in ("free", "zero"):
            continue
        if sp in prev_a_req and x_in != prev_a_req[sp]:
            bad_chain += 1
            if bad_chain <= 6:
                print(f"  CHAIN BREAK spindle {sp}: x_in {x_in} != prev a_req {prev_a_req[sp]}")
        else:
            ok_chain += 1
        prev_a_req[sp] = a_req
    print(f"== cache property ==  chained {ok_chain}, breaks {bad_chain}")
    print(f"  initial x per spindle: { {s: init_x.get(s) for s in (33, 48, 71)} }")
    print(f"  temp_in per spindle constant: "
          f"{ {s: len(temps.get(s, ())) == 1 for s in (33, 48, 71)} }  { {s: sorted(temps.get(s, [])) for s in (33, 48, 71)} }")

    # -- demand list for the model --------------------------------------------
    # row -> (kind, spindle|None, a_req, model_cost)
    demands: list[tuple[str, int | None, int, int]] = []
    real_entry_solve = 0
    for r in seq:
        kind, a_req, meta, cost = r[0], r[3], r[5], r[6]
        if kind == "reset94":
            demands.append(("reset94", None, 0, cost))
            continue
        if meta is None or meta[1] is None:
            demands.append((kind, None, a_req, cost))
            continue
        branch, sp = meta[0], meta[1]
        if branch in ("free", "zero"):
            demands.append((kind, None, a_req, 3))
            continue
        demands.append((kind, sp, a_req, meta[2] + meta[3]))
        real_entry_solve += meta[2] + meta[3]
    print(f"== real costs ==  entry+solve ops in plan: {real_entry_solve}")

    sps = [33, 48, 71]
    zlen = {33: 3, 48: 5, 71: 4}
    temp_sp = {s: (sorted(temps.get(s, {0}))[0]) for s in sps}
    values = sorted({d[2] for d in demands if d[1] is not None} | set(init_x.values()))
    print(f"== cost tables ==  {len(values)} values x {len(sps)} spindles")
    cost: dict[int, dict[int, dict[int, int]]] = {}
    for sp in sps:
        t = temp_sp[sp]
        tab = {}
        for v in values:
            rt = {}
            for w in values:
                try:
                    rt[w] = zlen[sp] + len(CS.solve_sp(0, t, v, w))
                except RuntimeError:
                    rt[w] = INF
            tab[v] = rt
        cost[sp] = tab
    print("  tables done")

    # -- model greedy ----------------------------------------------------------
    state = dict(init_x)
    greedy_model = 0
    for kind, sp, a_req, real_len in demands:
        if sp is None:
            greedy_model += real_len
            continue
        opts = [(cost[s].get(state.get(s), {}).get(a_req, INF), s) for s in sps]
        c, chosen = min(opts)
        if c >= INF:
            greedy_model += real_len
            continue
        greedy_model += c
        state[chosen] = a_req
    print(f"  model-greedy total (z-entry):  {greedy_model}")

    # -- beam search over cache states ----------------------------------------
    beam: dict[tuple[int, int, int], int] = {(init_x[33], init_x[48], init_x[71]): 0}
    BEAM = 30000
    for kind, sp, a_req, real_len in demands:
        if sp is None:
            beam = {k: v + real_len for k, v in beam.items()}
            continue
        nxt: dict[tuple[int, int, int], int] = {}
        if kind in ("sd94", "final94"):
            for (x33, x48, x71), c in beam.items():
                nc = c + cost[71].get(x71, {}).get(a_req, INF)
                if nc >= INF:
                    continue
                k2 = (x33, x48, a_req)
                if nc < nxt.get(k2, INF):
                    nxt[k2] = nc
        else:
            for (x33, x48, x71), c in beam.items():
                for i, x in enumerate((x33, x48, x71)):
                    s = sps[i]
                    nc = c + cost[s].get(x, {}).get(a_req, INF)
                    if nc >= INF:
                        continue
                    lst = [x33, x48, x71]
                    lst[i] = a_req
                    k2 = tuple(lst)
                    if nc < nxt.get(k2, INF):
                        nxt[k2] = nc
        if not nxt:
            print("  BEAM COLLAPSED (unreachable demand) — abort")
            return
        beam = dict(sorted(nxt.items(), key=lambda kv: kv[1])[:BEAM])
    beam_best = min(beam.values())
    print(f"  beam-DP best (z-entry model):   {beam_best}")
    print(f"== policy gain bound ==  model: {greedy_model - beam_best} ops "
          f"(k=19 needs >= 80 on the write phase)")

    import json
    print(f"  sim_ops total (write phase): {sum(ctx['simlens'])} in {len(ctx['simlens'])} calls")
    (HERE / f"out_simlens{args.tag}.json").write_text(json.dumps(sorted(ctx["simlens"])))
    out = [list(r) for r in seq]
    for r in out:
        if len(r) > 5 and isinstance(r[5], tuple):
            r[5] = list(r[5])
    (HERE / f"out_demand{args.tag}.json").write_text(json.dumps(out))
    print(f"  demand sequence dumped: {len(out)} rows -> out_demand{args.tag}.json")


if __name__ == "__main__":
    main()
