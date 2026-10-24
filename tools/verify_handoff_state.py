#!/usr/bin/env python3
"""Handoff-state gate for suffix-shifted Classic Malbolge programs.

Compressing a program by cutting a suffix and moving it down by ``delta`` cells is
only semantics-preserving if, at the moment execution reaches the shifted suffix,
the machine state equals the reference state after the same shift:

  * the program counter is the reference cell minus ``delta``;
  * the registers ``a`` and ``d`` hold the same (shifted) values;
  * every cell above the reference image that the reference preamble modified is
    installed at ``addr - delta`` with the shifted value.

This gate compares the two states and fails closed. It is the check the
2026-10-19 compact-cat pilot (``artifacts/candidate_cat_7893b.mal``) never had:
that candidate reaches its loop with ``d = 98`` instead of the required ``57,377``
and installs 0 of the reference's 124 variables.

Usage:
  python3 tools/verify_handoff_state.py \
      --reference reference/malbolge_org/cat.mal --reference-cell 9067 \
      --candidate artifacts/candidate_cat_7893b.mal --delta 1598

Exit codes: 0 = state matches, 1 = mismatch, 2 = invalid input or unreachable cell.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from constants import XLAT1, XLAT2, MEM_SIZE, crazy_op, rot_op


def load_program(path: Path) -> tuple[list[int], list[int]]:
    """Return (clean cells, fully initialised memory) for a Malbolge source."""
    raw = path.read_bytes()
    cells: list[int] = []
    for offset, byte in enumerate(raw):
        if chr(byte).isspace():
            continue
        if not (33 <= byte <= 126):
            raise ValueError(f"{path}: non-printable source byte 0x{byte:02x} at offset {offset}")
        cells.append(byte)
    if len(cells) < 2:
        raise ValueError(f"{path}: need at least two program cells, found {len(cells)}")
    return cells, memory_from_cells(cells)


def memory_from_cells(cells: list[int]) -> list[int]:
    """Build fully initialised Malbolge memory from already-loaded program cells."""
    mem = list(cells) + [0] * (MEM_SIZE - len(cells))
    for index in range(len(cells), MEM_SIZE):
        mem[index] = crazy_op(mem[index - 1], mem[index - 2])
    return mem


def run_to_cell(mem: list[int], target_cell: int, limit: int = 1_000_000) -> tuple[int, int, int, int, str]:
    """Execute until the program counter reaches ``target_cell``, without executing it."""
    a = c = d = 0
    for step in range(limit):
        if c == target_cell:
            return a, c, d, step, "AT_CELL"
        if not (33 <= mem[c] <= 126):
            return a, c, d, step, f"NONPRINTABLE_PC cell={c} value={mem[c]}"
        instruction = XLAT1[(mem[c] - 33 + c) % 94]
        if instruction == "j":
            d = mem[d]
        elif instruction == "i":
            c = mem[d]
        elif instruction == "*":
            a = mem[d] = rot_op(mem[d])
        elif instruction == "p":
            a = mem[d] = crazy_op(a, mem[d])
        elif instruction == "/":
            a = 59048
        elif instruction == "v":
            return a, c, d, step, f"HALT at cell {c} step {step}"
        if not (33 <= mem[c] <= 126):
            return a, c, d, step, f"INVALID_ENCRYPTION cell={c} value={mem[c]} step {step}"
        mem[c] = ord(XLAT2[mem[c] - 33])
        c = (c + 1) % MEM_SIZE
        d = (d + 1) % MEM_SIZE
    return a, c, d, limit, f"UNREACHED after {limit} steps"


def shifted_value(value: int, delta: int, value_floor: int) -> int:
    """Apply the shift rule used by the compact-cat generator to a stored value."""
    return value - delta if value >= value_floor else value


def compare_handoff(
    *,
    reference_mem: list[int],
    reference_init: list[int],
    reference_cells: int,
    candidate_mem: list[int],
    candidate_cells: int,
    delta: int,
    reference_cell: int,
    candidate_cell: int,
    reference_regs: tuple[int, int],
    candidate_regs: tuple[int, int],
    value_floor: int,
    max_rows: int = 10,
) -> dict:
    """Pure comparison of two handoff states; no I/O, used by the CLI and the tests."""
    a_ref, d_ref = reference_regs
    a_cand, d_cand = candidate_regs
    rows: list[dict] = []

    def add(cell: int, expected: int, actual: int, reason: str) -> None:
        if len(rows) < max_rows:
            rows.append({"cell": cell, "expected": expected, "actual": actual, "reason": reason})

    expected_candidate_cell = reference_cell - delta
    cell_match = expected_candidate_cell == candidate_cell
    if not cell_match:
        add(candidate_cell, expected_candidate_cell, candidate_cell, "program counter")

    register_mismatches = []
    if a_ref != a_cand:
        register_mismatches.append({"register": "a", "reference": a_ref, "candidate": a_cand})
    if d_ref - delta != d_cand:
        register_mismatches.append({"register": "d", "reference": d_ref - delta, "candidate": d_cand})

    variables = {
        addr: reference_mem[addr]
        for addr in range(reference_cells, MEM_SIZE)
        if reference_mem[addr] != reference_init[addr]
    }

    installed = 0
    wrong = 0
    for addr, value in sorted(variables.items()):
        target = addr - delta
        expected = shifted_value(value, delta, value_floor)
        actual = candidate_mem[target]
        if actual == expected:
            installed += 1
        else:
            wrong += 1
            add(target, expected, actual, f"variable from cell {addr}")

    ok = cell_match and not register_mismatches and wrong == 0
    return {
        "ok": ok,
        "delta": delta,
        "value_floor": value_floor,
        "reference_cell": reference_cell,
        "candidate_cell": candidate_cell,
        "expected_candidate_cell": expected_candidate_cell,
        "reference_image_cells": reference_cells,
        "candidate_image_cells": candidate_cells,
        "registers": {"reference": {"a": a_ref, "d": d_ref}, "candidate": {"a": a_cand, "d": d_cand}},
        "register_mismatches": register_mismatches,
        "variables_total": len(variables),
        "variables_installed": installed,
        "variables_wrong": wrong,
        "mismatches": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--reference-cell", required=True, type=int, help="loop entry cell in the reference")
    parser.add_argument("--candidate-cell", type=int, default=None, help="default: reference cell - delta")
    parser.add_argument("--delta", required=True, type=int, help="cells the suffix was moved down")
    parser.add_argument("--value-floor", type=int, default=None,
                        help="stored values >= this floor are shifted by delta (default: reference cell)")
    parser.add_argument("--step-limit", type=int, default=1_000_000)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.delta <= 0:
        print("INVALID: --delta must be positive", file=sys.stderr)
        return 2
    candidate_cell = args.candidate_cell if args.candidate_cell is not None else args.reference_cell - args.delta
    value_floor = args.value_floor if args.value_floor is not None else args.reference_cell

    try:
        ref_cells, ref_mem = load_program(args.reference)
        ref_init = list(ref_mem)
        cand_cells, cand_mem = load_program(args.candidate)
    except (OSError, ValueError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2

    a_ref, c_ref, d_ref, step_ref, status_ref = run_to_cell(ref_mem, args.reference_cell, args.step_limit)
    if status_ref != "AT_CELL":
        print(f"INVALID: reference never reached cell {args.reference_cell}: {status_ref}", file=sys.stderr)
        return 2
    a_cand, c_cand, d_cand, step_cand, status_cand = run_to_cell(cand_mem, candidate_cell, args.step_limit)
    if status_cand != "AT_CELL":
        print(f"MISMATCH: candidate never reached cell {candidate_cell}: {status_cand}", file=sys.stderr)
        return 1

    report = compare_handoff(
        reference_mem=ref_mem,
        reference_init=ref_init,
        reference_cells=len(ref_cells),
        candidate_mem=cand_mem,
        candidate_cells=len(cand_cells),
        delta=args.delta,
        reference_cell=c_ref,
        candidate_cell=c_cand,
        reference_regs=(a_ref, d_ref),
        candidate_regs=(a_cand, d_cand),
        value_floor=value_floor,
    )
    report["steps"] = {"reference": step_ref, "candidate": step_cand}
    report["files"] = {"reference": str(args.reference), "candidate": str(args.candidate)}

    print(f"reference {args.reference}: cell {c_ref} at step {step_ref}, a={a_ref}, d={d_ref}")
    print(f"candidate {args.candidate}: cell {c_cand} at step {step_cand}, a={a_cand}, d={d_cand}")
    print(f"delta {args.delta}; expected candidate cell {args.reference_cell - args.delta}")
    print(f"variables installed: {report['variables_installed']}/{report['variables_total']}")
    for mismatch in report["register_mismatches"]:
        print(f"  register {mismatch['register']}: expected {mismatch['reference']} got {mismatch['candidate']}")
    for row in report["mismatches"]:
        print(f"  cell {row['cell']}: expected {row['expected']} got {row['actual']} ({row['reason']})")
    print("HANDOFF MATCH" if report["ok"] else "HANDOFF MISMATCH")

    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
