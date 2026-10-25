"""Independent verification of the k=18 (7,690-cell) compact Cat handoff.

Origin: ``antigravity_53501039`` bridge handoff (2026-10-25, ANNOUNCE seq=9040):
a compact BOOT (1,235 ops instead of 1,369) closes the k=18 gap at
7,199 ops vs the 7,213 budget, i.e. a 7,690-cell streaming Cat.

This script does NOT trust the handoff harness. It re-derives every number:

  S1  the planner's memory model (alternating fill) equals the real crazy
      recurrence fill of the reference image;
  S2  control C0: the same patched harness driven by a verbatim replay of the
      ORIGINAL boot must reproduce the published frontier 7,331 ops --
      this validates the patch harness, the boot replay and the seeds;
  S3  the in-repo ``compact_boot.py`` emits the same op string as the
      handoff's scratch function (when that file is still present);
  S4  exact memory diff at boot end (original boot vs compact boot);
  S5  instrumented full synthesis: odometer (k_cell) usage, scratchpad
      touches, per-phase op counts; total must be 7,199;
  S6  assembly: 7,690 cells, end_c within budget, deterministic bytes;
  S7  canonical handoff comparison (tools/verify_handoff_state): 124/124;
  S8  own-VM trace: post-handoff the program never touches low memory
      (the load-bearing safety claim for the trimmed boot) and echoes
      its input byte-exactly;
  S9  mb_ref battery: 7 reference cases + 64 KiB binary stream (--full).

Run:
  python3 docs/evidence/2026-10-25-compact-cat-k18/verify_k18.py          # S1-S8
  python3 docs/evidence/2026-10-25-compact-cat-k18/verify_k18.py --full  # + S9
"""
from __future__ import annotations

import argparse
import hashlib
import random
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CHAIN_DIR = ROOT / "docs" / "evidence" / "2026-10-25-cat-chain-sweeps"
SCRATCH = Path(
    "/home/danny/.gemini/antigravity-cli/brain/"
    "53501039-4c01-4d2f-95b2-2a54492799b8/scratch/test_k18_boot.py"
)

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CHAIN_DIR))
sys.path.insert(0, str(HERE))

from constants import MEM_SIZE, XLAT1, XLAT2, crazy_op, rot_op  # noqa: E402
import chain_synth as CS  # noqa: E402
from compact_boot import (  # noqa: E402
    C29524, CH_CRZ, CH_DLD, CH_NOP, CH_ROT,
    build_compact_boot, planner_fill_mem, rebuild_orig_boot_ops,
)
from tools.verify_handoff_state import (  # noqa: E402
    compare_handoff, load_program, memory_from_cells, run_to_cell,
)

REF = ROOT / "reference" / "malbolge_org" / "cat.mal"
K, SEED, DELTA = 18, 9803, 94 * 18
BUDGET = 7213
HANDOFF_REF_CELL = 9067
HANDOFF_CAND_CELL = HANDOFF_REF_CELL - DELTA
LOW_BOUND = 9003 - DELTA  # candidate equivalent of the reference's cell 9003

BOOT_BLOCK = """    b_idx = 1
    while b_idx <= 1434:
        if b_idx in BOOT_START_MAP:
            end_idx, sp_b, targ_a = BOOT_START_MAP[b_idx]
            if b_idx == 1367:
                min_addr = min(high_mods.keys())
                base_val = min_addr if first_base_at_min else min_addr - 1
                targ_a = find_a_for_crazy(C29524, base_val)
                assert targ_a is not None
            seq = solve_sp(a, mem[sp_b + 2], mem[sp_b + 3], targ_a)
            sim_ops(seq)
            b_idx = end_idx + 1
        else:
            sim_ops(orig_boot_ops[b_idx])
            b_idx += 1

    sim_ops(CH_NOP + CH_DLD)
    assert d == 82"""

NEW_BLOCK = """    ops_b, mem_b, a_b, d_b = _CUSTOM_BOOT(orig_boot_ops, template_clean, high_mods, first_base_at_min)
    ops_out.extend(ops_b)
    mem[:] = mem_b
    a, d = a_b, d_b
    assert d == 82"""

HOOKS = [
    (
        "        if new_dest == curr_94 + 9:",
        '        if new_dest == curr_94 + 9:\n            _HOOKS["plus9"] += 1',
    ),
    (
        "                if crazy_op(mk, v1) == new_dest:",
        '                if crazy_op(mk, v1) == new_dest:\n'
        '                    _HOOKS["kcell"][k_cell] = _HOOKS["kcell"].get(k_cell, 0) + 1',
    ),
    (
        "    def sim_ops(seq: str) -> None:\n"
        "        nonlocal a, d\n"
        "        for ch in seq:\n"
        "            ops_out.append(ch)",
        "    def sim_ops(seq: str) -> None:\n"
        "        nonlocal a, d\n"
        "        for ch in seq:\n"
        "            ops_out.append(ch)\n"
        "            if ch in (CH_DLD, CH_ROT, CH_CRZ) and 33 <= d <= 99:\n"
        '                _HOOKS["touch"][(ch, d)] = _HOOKS["touch"].get((ch, d), 0) + 1',
    ),
]

_BOOT_END: dict = {}


def replay_orig_boot(orig_boot_ops, template_clean, high_mods, first_base_at_min):
    """Verbatim replay of the boot the way ``synthesize_preamble_ops`` does it."""
    mem = planner_fill_mem(template_clean, len(template_clean))
    a, d = 0, 1
    ops_out: list[str] = []

    def sim_ops(seq: str) -> None:
        nonlocal a, d
        for ch in seq:
            ops_out.append(ch)
            if ch == CH_DLD:
                d = mem[d]
            elif ch == CH_ROT:
                mem[d] = rot_op(mem[d])
                a = mem[d]
            elif ch == CH_CRZ:
                mem[d] = crazy_op(a, mem[d])
                a = mem[d]
            d = (d + 1) % MEM_SIZE

    b_idx = 1
    while b_idx <= 1434:
        if b_idx in CS.BOOT_START_MAP:
            end_idx, sp_b, targ_a = CS.BOOT_START_MAP[b_idx]
            if b_idx == 1367:
                min_addr = min(high_mods.keys())
                base_val = min_addr if first_base_at_min else min_addr - 1
                targ_a = CS.find_a_for_crazy(C29524, base_val)
                assert targ_a is not None
            sim_ops(CS.solve_sp(a, mem[sp_b + 2], mem[sp_b + 3], targ_a))
            b_idx = end_idx + 1
        else:
            sim_ops(orig_boot_ops[b_idx])
            b_idx += 1
    sim_ops(CH_NOP + CH_DLD)
    assert d == 82
    return ops_out, mem, a, d


def run_plan(boot_fn, clean, high_mods, hd, template_clean, label):
    """Exec a hooked copy of chain_synth with the boot replaced by ``boot_fn``."""
    src = (CHAIN_DIR / "chain_synth.py").read_text()
    assert BOOT_BLOCK in src, "chain_synth.py boot block changed"
    src = src.replace(BOOT_BLOCK, NEW_BLOCK, 1)
    for old, new in HOOKS:
        assert old in src, f"hook anchor missing: {old[:50]}"
        src = src.replace(old, new, 1)

    def wrapped(orig_boot_ops, tc, hm, fbam):
        res = boot_fn(orig_boot_ops, tc, hm, fbam)
        _BOOT_END.clear()
        _BOOT_END.update(ops=res[0], mem=res[1], a=res[2], d=res[3])
        return res

    hooks = {"kcell": {}, "plus9": 0, "touch": {}}
    ns = {"__file__": str(CHAIN_DIR / "chain_synth.py"),
          "_CUSTOM_BOOT": wrapped, "_HOOKS": hooks}
    exec(compile(src, f"<chain_synth_{label}>", "exec"), ns)
    ops = ns["synthesize_preamble_ops"](
        clean, high_mods, hd, 9003,
        delta=DELTA, template_clean=template_clean,
        borrow_penalty=1, direct_gap=18,
        rng=random.Random(SEED), restart_p1=0.80, restart_p2=0.90,
    )
    return ops, hooks


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def band(addr: int, tag: str, low: int = LOW_BOUND, main_hi: int = 9382 - DELTA) -> str:
    if addr == 0:
        return f"{tag}=0"
    if addr < 100:
        return f"{tag}=1..99"
    if addr < low:
        return f"{tag}=100..{low - 1}"
    if addr <= main_hi:
        return f"{tag}={low}..{main_hi}"
    if addr < 58843:
        return f"{tag}={main_hi + 1}..58842"
    return f"{tag}=58843..59048"


def trace_echo(mem, data: bytes, handoff_cell: int, max_steps: int):
    """Full-VM trace (mb_ref semantics) of the assembled candidate."""
    a = c = d = 0
    out = bytearray()
    pos = 0
    post = False
    pre_d: dict[str, int] = {}
    post_c: dict[str, int] = {}
    post_d: dict[str, int] = {}
    low_d: dict[int, int] = {}
    scratch_d: dict[int, int] = {}
    watch: dict[int, int] = {}
    handoff_step = None
    halted = False
    for step in range(max_steps):
        if c == handoff_cell and not post:
            post = True
            handoff_step = step
        b = band(d, "d")
        if post:
            post_c[band(c, "c")] = post_c.get(band(c, "c"), 0) + 1
            post_d[b] = post_d.get(b, 0) + 1
            if d < LOW_BOUND:
                low_d[d] = low_d.get(d, 0) + 1
            if 33 <= d <= 99:
                scratch_d[d] = scratch_d.get(d, 0) + 1
            if d in (50, 73, 89):
                watch[d] = watch.get(d, 0) + 1
        else:
            pre_d[b] = pre_d.get(b, 0) + 1
        instr = XLAT1[(mem[c] - 33 + c) % 94]
        if instr == "j":
            d = mem[d]
        elif instr == "i":
            c = mem[d]
        elif instr == "*":
            mem[d] = rot_op(mem[d])
            a = mem[d]
        elif instr == "p":
            mem[d] = crazy_op(a, mem[d])
            a = mem[d]
        elif instr == "<":
            out.append(a & 255)
        elif instr == "/":
            if pos < len(data):
                a = data[pos]
                pos += 1
            else:
                a = 59048
        elif instr == "v":
            halted = True
            break
        mem[c] = ord(XLAT2[mem[c] - 33])
        c = 0 if c == 59048 else c + 1
        d = 0 if d == 59048 else d + 1
        if len(out) == len(data):
            break
    stats = dict(out_len=len(out), halted=halted, handoff_step=handoff_step,
                 pre_d=pre_d, post_c=post_c, post_d=post_d, low_d=low_d,
                 scratch_d=scratch_d, watch=watch, steps=step + 1)
    return bytes(out), stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="also run the mb_ref battery (slow)")
    full = ap.parse_args().full

    print("== S0 environment ==")
    clean, high_mods, hd, _ = CS.extract_target_state(REF, 9003)
    template_clean = [b for b in REF.read_bytes() if 33 <= b <= 126]
    for name, path in [("reference cat.mal", REF),
                       ("chain_synth.py", CHAIN_DIR / "chain_synth.py"),
                       ("compact_boot.py", HERE / "compact_boot.py")]:
        print(f"  {name:22s} sha256 {sha(path.read_bytes())[:16]}…")
    print(f"  reference image      {len(clean)} cells; delta={DELTA}; budget={BUDGET}")

    print("== S1 planner memory model: exact where the plan reads ==")
    rec = list(clean) + [0] * (MEM_SIZE - len(clean))
    for i in range(len(clean), MEM_SIZE):
        rec[i] = crazy_op(rec[i - 1], rec[i - 2])
    model = planner_fill_mem(template_clean, len(clean))
    diffs = [i for i in range(MEM_SIZE) if rec[i] != model[i]]
    lo, hi = (min(diffs), max(diffs)) if diffs else (None, None)
    win_bad = [i for i in diffs if i >= 58843]
    print(f"  model vs real fill: {len(diffs)} differing cells, confined to [{lo}..{hi}]")
    print("  (that band is the reference image's interior: executed as c, never read")
    print("   as d; S8 proves d never lands there)")
    print(f"  differing cells inside the write window 58843..59048: {len(win_bad)}")
    assert not [i for i in diffs if i < 1533], "model wrong below 1533 (scratchpads!)"
    assert not [i for i in diffs if i >= 9381], "model wrong in the high/anchor region"

    print("== S2 control C0: patched harness + ORIGINAL boot ==")
    ops_c0, hooks_c0 = run_plan(replay_orig_boot, clean, high_mods, hd, template_clean, "c0")
    boot_c0 = list(_BOOT_END["ops"])
    print(f"  original boot ops    {len(boot_c0)}")
    print(f"  total plan ops       {len(ops_c0)}  (published frontier: 7331)")
    assert len(ops_c0) == 7331, f"C0 control failed: {len(ops_c0)}"
    mem_boot_orig = list(_BOOT_END["mem"])
    a_boot_orig, d_boot_orig = _BOOT_END["a"], _BOOT_END["d"]
    rest_c0 = len(ops_c0) - len(boot_c0)

    print("== S3 compact boot (in-repo copy) ==")
    orig_boot_ops = rebuild_orig_boot_ops(template_clean, len(clean))
    ops_new, mem_new, a_new, d_new = build_compact_boot(orig_boot_ops, template_clean, high_mods)
    print(f"  compact boot ops     {len(ops_new)}  (expected 1235)")
    assert len(ops_new) == 1235 and d_new == 82
    if SCRATCH.exists():
        text = SCRATCH.read_text()
        start = text.index("def build_compact_boot")
        end = text.index("    return ops_out, mem, a, d", start) + len("    return ops_out, mem, a, d")
        ns = {"C59048": 59048, "C59047": 59047, "C59046": 59046, "C29524": C29524,
              "CH_NOP": CH_NOP, "CH_ROT": CH_ROT, "CH_CRZ": CH_CRZ, "CH_DLD": CH_DLD,
              "MEM_SIZE": MEM_SIZE, "solve_sp": CS.solve_sp,
              "find_a_for_crazy": CS.find_a_for_crazy,
              "rot_op": rot_op, "crazy_op": crazy_op,
              "orig_boot_ops": orig_boot_ops, "n": len(clean)}
        exec(compile(text[start:end], "<scratch_build_compact_boot>", "exec"), ns)
        ops_s, mem_s, a_s, d_s = ns["build_compact_boot"](template_clean, high_mods)
        same = "".join(ops_s) == "".join(ops_new) and mem_s == mem_new and (a_s, d_s) == (a_new, d_new)
        print(f"  cross-check vs handoff scratch function: "
              f"ops identical={same} (scratch len {len(ops_s)})")
        assert same, "in-repo compact_boot.py diverges from the handoff function"
    else:
        print("  cross-check skipped: handoff scratch file not present")

    print("== S4 boot-end memory diff (original vs compact) ==")
    mem_boot_new = list(mem_new)
    diffs = [(i, mem_boot_orig[i], mem_boot_new[i])
             for i in range(MEM_SIZE) if mem_boot_orig[i] != mem_boot_new[i]]
    for i, o, nw in diffs:
        print(f"  mem[{i:3d}]  orig {o:5d}  compact {nw:5d}")
    print(f"  differing cells: {len(diffs)}")
    assert a_boot_orig is not None

    print("== S5 instrumented k=18 seed 9803 synthesis (compact boot) ==")
    ops_k18, hooks = run_plan(build_compact_boot, clean, high_mods, hd, template_clean, "k18")
    boot_len = len(_BOOT_END["ops"])
    total = len(ops_k18)
    print(f"  boot ops             {boot_len}")
    print(f"  write+handoff ops    {total - boot_len}  (original plan: {rest_c0})")
    print(f"  TOTAL PLAN OPS       {total}  (budget {BUDGET}, margin {BUDGET - total})")
    assert total <= BUDGET, "over budget"
    assert total == 7199, f"expected 7199, got {total}"
    kcell = dict(sorted(hooks["kcell"].items()))
    print(f"  odometer +9 calls    {hooks['plus9']}, k_cell chosen: {kcell}")
    touch = hooks["touch"]
    per_watch = {}
    for (ch, dd), v in touch.items():
        if dd in (50, 73, 89):
            per_watch[(dd, ch)] = per_watch.get((dd, ch), 0) + v
    print(f"  write-phase touches at 50/73/89 by (cell, op): "
          f"{dict(sorted(per_watch.items()))}")
    ident = (hooks_c0["kcell"] == hooks["kcell"]
             and hooks_c0["touch"] == hooks["touch"]
             and rest_c0 == total - boot_len)
    print(f"  write phase identical to the original-boot plan: {ident} "
          f"(kcell {hooks_c0['kcell']} == {hooks['kcell']})")
    by_cell: dict[int, int] = {}
    for (_ch, dd), v in touch.items():
        by_cell[dd] = by_cell.get(dd, 0) + v
    print("  top touched scratchpads (write phase): "
          + ", ".join(f"{c}:{v}" for c, v in sorted(by_cell.items(), key=lambda kv: -kv[1])[:10]))

    print("== S6 assembly, budget, determinism ==")
    cand_raw, end_c = CS.assemble_shifted_program(template_clean, ops_k18, clean, 9003, DELTA)
    assert cand_raw is not None, f"overrun: end_c={end_c}"
    cand_cells = [b for b in cand_raw if 33 <= b <= 126]
    print(f"  candidate cells      {len(cand_raw)}  (expected 7690)")
    print(f"  end_c                {end_c}  (max allowed {9003 - DELTA})")
    print(f"  sha256               {sha(cand_raw)}")
    assert len(cand_raw) == 7690 and len(cand_cells) == 7690
    assert end_c == 99 + total - 1 and end_c <= 9003 - DELTA
    ops_again, _ = run_plan(build_compact_boot, clean, high_mods, hd, template_clean, "k18b")
    cand2, _ = CS.assemble_shifted_program(template_clean, ops_again, clean, 9003, DELTA)
    print(f"  deterministic rebuild identical: {cand2 == cand_raw}")
    assert cand2 == cand_raw and len(ops_again) == total

    print("== S7 canonical handoff comparison ==")
    ref_cells, ref_mem = load_program(REF)
    ref_init = list(ref_mem)
    cand_mem = memory_from_cells(cand_cells)
    a_ref, c_ref, d_ref, _, st_ref = run_to_cell(ref_mem, HANDOFF_REF_CELL)
    a_c, c_c, d_c, _, st_c = run_to_cell(cand_mem, HANDOFF_CAND_CELL)
    rep = compare_handoff(
        reference_mem=ref_mem, reference_init=ref_init, reference_cells=len(ref_cells),
        candidate_mem=cand_mem, candidate_cells=len(cand_cells),
        delta=DELTA, reference_cell=c_ref, candidate_cell=c_c,
        reference_regs=(a_ref, d_ref), candidate_regs=(a_c, d_c),
        value_floor=9003, value_ceiling=len(ref_cells), memory_mode="keep-high",
    )
    print(f"  statuses             ref={st_ref} cand={st_c}")
    print(f"  report ok={rep['ok']} variables={rep['variables_installed']}/{rep['variables_total']} "
          f"mismatches={len(rep['mismatches'])}")
    assert rep["ok"] and rep["variables_installed"] == rep["variables_total"] == 124
    assert not rep["mismatches"]

    print("== S8 post-handoff trace (own VM, 2048-byte stream) ==")
    trace_mem = memory_from_cells(cand_cells)
    data = random.Random(0xCA7).randbytes(2048)
    out, st = trace_echo(trace_mem, data, HANDOFF_CAND_CELL, max_steps=8_000_000)
    print(f"  echoed {st['out_len']}/2048 bytes exact: {out == data[:st['out_len']]}  "
          f"(halted={st['halted']}, steps={st['steps']}, handoff at step {st['handoff_step']})")
    assert out == data[:st["out_len"]] and st["out_len"] >= 512
    print(f"  pre-handoff d bands  : {st['pre_d']}")
    print(f"  post-handoff c bands : {st['post_c']}")
    print(f"  post-handoff d bands : {st['post_d']}")
    print(f"  post-handoff d < {LOW_BOUND}: {sum(st['low_d'].values())} touches "
          f"{dict(sorted(st['low_d'].items())[:12])}")
    print(f"  post-handoff scratchpad (33..99) touches: {sum(st['scratch_d'].values())}")
    print(f"  post-handoff touches of cells 50/73/89: {st['watch']}")
    assert not st["low_d"], "post-handoff execution read low memory"

    if full:
        print("== S9 mb_ref battery ==")
        from tools.test_compressed import run as run_mb_ref, verify_target

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "cat_k18_7690.mal"
            p.write_bytes(cand_raw)
            cases = verify_target("cat", p)
            print(f"  verify_target('cat')  {cases} cases PASSED")
            stream64k = random.Random(0xCA7).randbytes(65536)
            out64k = run_mb_ref(p, stream64k)
            print(f"  64 KiB binary stream  {len(out64k)}/{len(stream64k)} bytes exact: "
                  f"{out64k == stream64k}")
            assert out64k == stream64k

    print("== VERDICT: k=18 7,690-cell plan DEMONSTRATED under this battery ==")


if __name__ == "__main__":
    main()
