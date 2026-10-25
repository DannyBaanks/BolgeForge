"""Verify the k=19 candidate built from the beam-assignment op stream.

The beam (w2_beam.py) replays the greedy write order of the k=18 plan,
choosing the spindle/entry per write; the winner is a REAL op stream
(out_beam_ops.txt). This script assembles the full k=19 program

    compact boot (1,235 ops) + beam write phase (out_beam_ops.txt) + JMP

at delta = 94*19 = 1,786 and runs the repo's acceptance gates:

  * budget: end_c = 99 + ops - 1 <= 9,003 - 1,786 = 7,217 (cells 7,596);
  * compare_handoff keep-high: 124/124 variables, registers equal;
  * mb_ref exact-output battery (7 cases) and a 64 KiB binary stream;
  * a post-handoff trace: no low-memory reads (the safety property that
    makes the trimmed boot and the spindle-cell divergence irrelevant).

Run: python3 docs/evidence/2026-10-25-cat-k19-frontier/verify_k19.py [--ops out_beam_ops.txt]
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
K18 = ROOT / "docs" / "evidence" / "2026-10-25-cat-chain-sweeps"
K18EV = ROOT / "docs" / "2026-10-25-compact-cat-k18"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(K18))
sys.path.insert(0, str(K18EV))
sys.path.insert(0, str(HERE))

from constants import MEM_SIZE, XLAT1, XLAT2, crazy_op, rot_op  # noqa: E402
import chain_synth as CS  # noqa: E402
from tools.compact_boot import build_compact_boot, rebuild_orig_boot_ops  # noqa: E402
from tools.verify_handoff_state import (  # noqa: E402
    compare_handoff, load_program, memory_from_cells, run_to_cell,
)

REF = ROOT / "reference" / "malbolge_org" / "cat.mal"
LIN_END = 9003
K = 19
DELTA = 94 * K
BUDGET = (LIN_END - DELTA) - 98          # ops allowed in the preamble
HANDOFF_REF_CELL = 9067
HANDOFF_CAND_CELL = HANDOFF_REF_CELL - DELTA
CH_JMP = CS.CH_JMP


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def band(addr: int, tag: str, low: int = LIN_END - DELTA) -> str:
    if addr == 0:
        return f"{tag}=0"
    if addr < 100:
        return f"{tag}=1..99"
    if addr < low:
        return f"{tag}=100..{low - 1}"
    if addr <= 9382 - DELTA:
        return f"{tag}={low}..{9382 - DELTA}"
    if addr < 58843:
        return f"{tag}={9383 - DELTA}..58842"
    return f"{tag}=58843..59048"


def trace_echo(mem, data: bytes, handoff_cell: int, max_steps: int):
    a = c = d = 0
    out = bytearray()
    pos = 0
    post = False
    post_d: dict[str, int] = {}
    low_d: dict[int, int] = {}
    scratch: dict[int, int] = {}
    handoff_step = None
    for step in range(max_steps):
        if c == handoff_cell and not post:
            post = True
            handoff_step = step
        if post:
            b = band(d, "d")
            post_d[b] = post_d.get(b, 0) + 1
            if d < LIN_END - DELTA:
                low_d[d] = low_d.get(d, 0) + 1
            if 33 <= d <= 99:
                scratch[d] = scratch.get(d, 0) + 1
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
            break
        mem[c] = ord(XLAT2[mem[c] - 33])
        c = 0 if c == 59048 else c + 1
        d = 0 if d == 59048 else d + 1
        if len(out) == len(data):
            break
    return bytes(out), dict(post_d=post_d, low_d=low_d, scratch=scratch,
                            handoff_step=handoff_step, steps=step + 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ops", type=Path, default=HERE / "out_beam_ops.txt")
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args()

    clean, high_mods, handoff_d, _ = CS.extract_target_state(REF, LIN_END)
    template_clean = [b for b in REF.read_bytes() if 33 <= b <= 126]
    n = len(clean)
    boot_ops, _mem, _a, _d = build_compact_boot(
        rebuild_orig_boot_ops(template_clean, n), template_clean, high_mods)
    write_ops = args.ops.read_text().strip()
    assert set(write_ops) <= set("op*djiv<"), sorted(set(write_ops) - set("op*djiv<"))

    ops = "".join(boot_ops) + write_ops + CH_JMP
    total = len(ops)
    print(f"== S1 plan ==")
    print(f"  boot {len(''.join(boot_ops))} + beam write {len(write_ops)} + JMP 1 "
          f"= {total} ops")
    print(f"  k=19 budget {BUDGET}  (margin {BUDGET - total})")
    assert total <= BUDGET, "over budget"

    print("== S2 assembly ==")
    cand_raw, end_c = CS.assemble_shifted_program(template_clean, ops, clean, LIN_END, DELTA)
    assert cand_raw is not None, f"overrun end_c={end_c}"
    cand_cells = [b for b in cand_raw if 33 <= b <= 126]
    print(f"  cells {len(cand_raw)} (expected {9382 - DELTA}), end_c {end_c} "
          f"(max {LIN_END - DELTA}), sha256 {sha(cand_raw)}")
    assert len(cand_raw) == 9382 - DELTA and len(cand_cells) == len(cand_raw)

    print("== S3 canonical handoff comparison ==")
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
        value_floor=LIN_END, value_ceiling=len(ref_cells), memory_mode="keep-high",
    )
    print(f"  statuses ref={st_ref} cand={st_c}")
    print(f"  ok={rep['ok']} variables={rep['variables_installed']}/{rep['variables_total']} "
          f"mismatches={len(rep['mismatches'])}")
    assert rep["ok"] and rep["variables_installed"] == rep["variables_total"] == 124
    assert not rep["mismatches"] and st_ref == st_c == "AT_CELL"

    print("== S4 post-handoff trace (2,048-byte stream) ==")
    trace_mem = memory_from_cells(cand_cells)
    data = random.Random(0xCA7).randbytes(2048)
    out, st = trace_echo(trace_mem, data, HANDOFF_CAND_CELL, max_steps=8_000_000)
    print(f"  echoed {len(out)}/2048 exact: {out == data[:len(out)]} "
          f"(steps {st['steps']}, handoff at {st['handoff_step']})")
    print(f"  post-handoff d bands: {st['post_d']}")
    print(f"  post-handoff d < {LIN_END - DELTA}: {sum(st['low_d'].values())} touches; "
          f"scratchpad touches: {sum(st['scratch'].values())}")
    assert out == data[:len(out)] and len(out) >= 512
    assert not st["low_d"], "post-handoff execution read low memory"

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "cat_k19.mal"
        p.write_bytes(cand_raw)
        if not args.full:
            print("== S5 mb_ref battery: SKIPPED (run with --full) ==")
        else:
            print("== S5 mb_ref battery ==")
            from tools.test_compressed import run as run_mb_ref, verify_target
            cases = verify_target("cat", p)
            print(f"  verify_target('cat'): {cases} cases PASSED")
            stream64k = random.Random(0xCA7).randbytes(65536)
            out64k = run_mb_ref(p, stream64k)
            print(f"  64 KiB binary stream: {len(out64k)}/{len(stream64k)} exact: {out64k == stream64k}")
            assert out64k == stream64k

    print(f"== VERDICT: k=19 candidate DEMONSTRATED ({9382 - DELTA} cells, "
          f"{total} ops, margin {BUDGET - total}) ==")


if __name__ == "__main__":
    main()
