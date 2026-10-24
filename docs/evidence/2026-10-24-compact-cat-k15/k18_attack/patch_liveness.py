#!/usr/bin/env python3
"""Decisive test of the two cells the earlier liveness probe called dead.

Builds the k=18 plan that omits cells 58,844 and 59,046 from the installed
target table (seed 1435, borrow penalty 2, direct gap 18, restart thresholds
0.80/0.90), then compares the handoff state at the gate cell 7,375 after
patching the omitted cells with their reference 9,003 values.

Expected (2026-10-24):
  no patch          -> INVALID_ENCRYPTION at cell 58,844, value 29,443
  patch 58,844 only -> gate reached, 123/124 variables
  patch both        -> gate reached, 124/124 variables, a/d exact

The point: both cells are live.  No handoff exemption is legitimate.
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import search_synth as R
from constants import XLAT1, XLAT2, MEM_SIZE, crazy_op, rot_op
from tools.verify_handoff_state import compare_handoff, load_program, run_to_cell

REF = ROOT / 'reference' / 'malbolge_org' / 'cat.mal'
LIN_END = 9003
K = 18
DELTA = 94 * K
GATE_REF = 9067
GATE_CAND = GATE_REF - DELTA          # 7,375
FINAL_JMP_CELL = 99 + 7210 - 1        # 7,308, last preamble cell (7,210 ops)
DROP = {58844, 59046}


def continue_from(mem, a, c, d, target, limit=3_000_000):
    """Run from an explicit (a, c, d) state; stop before executing `target`."""
    for step in range(limit):
        if c == target:
            return a, c, d, step, 'AT_CELL'
        if not (33 <= mem[c] <= 126):
            return a, c, d, step, f'NONPRINT {c} {mem[c]}'
        ch = XLAT1[(mem[c] - 33 + c) % 94]
        if ch == 'j':
            d = mem[d]
        elif ch == 'i':
            c = mem[d]
        elif ch == '*':
            a = mem[d] = rot_op(mem[d])
        elif ch == 'p':
            a = mem[d] = crazy_op(a, mem[d])
        elif ch == '/':
            a = 59048
        elif ch == 'v':
            return a, c, d, step, f'HALT {c}'
        if not (33 <= mem[c] <= 126):
            return a, c, d, step, f'INVALID {c} {mem[c]}'
        mem[c] = ord(XLAT2[mem[c] - 33])
        c = (c + 1) % MEM_SIZE
        d = (d + 1) % MEM_SIZE
    return a, c, d, limit, 'LIMIT'


def build_candidate():
    clean, high, handoff_d, _ = R.extract_target_state(REF, LIN_END)
    template = [b for b in REF.read_bytes() if 33 <= b <= 126]
    high2 = {a: v for a, v in high.items() if a not in DROP}
    ops = R.synthesize_preamble_ops(
        clean, high2, handoff_d, LIN_END, delta=DELTA, template_clean=template,
        borrow_penalty=2, direct_gap=18, rng=random.Random(1435),
        restart_p1=0.80, restart_p2=0.90,
    )
    raw, end_c = R.assemble_shifted_program(template, ops, clean, LIN_END, DELTA)
    assert raw is not None, end_c
    path = Path('/tmp/opencode/cat_7690_119.mal')
    path.write_bytes(raw)
    return path, len(ops), end_c


def main() -> int:
    out, nops, end_c = build_candidate()
    print(f'candidate: {out} cells={out.stat().st_size} preamble_ops={nops} end_c={end_c}')

    _, ref_9003 = load_program(REF)
    a0, c0, d0, _, _ = run_to_cell(ref_9003, LIN_END)
    ref_at_9003 = list(ref_9003)

    _, ref_gate = load_program(REF)
    ar, cr, dr, _, _ = run_to_cell(ref_gate, GATE_REF)

    _, cand = load_program(out)
    for patch in [(), (58844,), (58844, 59046)]:
        mem = list(cand)
        ac, cc, dc, _, _ = run_to_cell(mem, FINAL_JMP_CELL)
        for cell in patch:
            mem[cell] = ref_at_9003[cell]
        # execute the final JMP at 7,308
        ch = XLAT1[(mem[cc] - 33 + cc) % 94]
        assert ch == 'i', ch
        cc = mem[dc]
        mem[cc] = ord(XLAT2[mem[cc] - 33])
        cc = (cc + 1) % MEM_SIZE
        dc = (dc + 1) % MEM_SIZE
        aa, ccell, dd, step, msg = continue_from(mem, ac, cc, dc, GATE_CAND)
        line = f'patch={patch!s:20s} result={msg:22s} step={step}'
        if msg == 'AT_CELL':
            report = compare_handoff(
                reference_mem=ref_gate, reference_init=load_program(REF)[1],
                reference_cells=len(load_program(REF)[0]),
                candidate_mem=mem, candidate_cells=len(cand),
                delta=DELTA, reference_cell=GATE_REF, candidate_cell=GATE_CAND,
                reference_regs=(ar, dr), candidate_regs=(aa, dd),
                value_floor=LIN_END, value_ceiling=len(load_program(REF)[0]),
                memory_mode='keep-high',
            )
            line += (f" a={'OK' if aa == ar else 'BAD'} d={'OK' if dd == dr else 'BAD'}"
                     f" variables={report['variables_installed']}/{report['variables_total']}")
        print(line)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
