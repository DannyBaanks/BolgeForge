#!/usr/bin/env python3
"""Strict Classic Malbolge cycle prover for the 90-byte truth machine.

The prover implements Olmstead's published loader/execution semantics (the same
behaviour as docs/audits/2026-10-20-e2e/olmstead_strict_mirror.c):

  * every source cell must decode, at its load address, to one of "ji*p</vo";
  * a nonprintable program counter stalls the machine (reported, never skipped);
  * after each instruction, mem[c] = xlat2[mem[c]-33]; c and d advance mod 59049.

For input '0' it requires a real HALT after printing exactly one '0'.
For input '1' it requires a repeated *full* machine state (a, c, d and all
59,049 memory cells). Deterministic repetition with a positive number of
emissions per period proves an infinite '1' stream.

Usage:
  python3 tools/prove_truth_machine.py artifacts/truth_machine_classic_90b.mal --json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

MEM_SIZE = 59049
XLAT1 = "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha"
XLAT2 = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
VALID = frozenset("ji*p</vo")
P9 = (1, 9, 81, 729, 6561)
CRAZY = (
    (4, 3, 3, 1, 0, 0, 1, 0, 0),
    (4, 3, 5, 1, 0, 2, 1, 0, 2),
    (5, 5, 4, 2, 2, 1, 2, 2, 1),
    (4, 3, 3, 1, 0, 0, 7, 6, 6),
    (4, 3, 5, 1, 0, 2, 7, 6, 8),
    (5, 5, 4, 2, 2, 1, 8, 8, 7),
    (7, 6, 6, 7, 6, 6, 4, 3, 3),
    (7, 6, 8, 7, 6, 8, 4, 3, 5),
    (8, 8, 7, 8, 8, 7, 5, 5, 4),
)


def crazy(x: int, y: int) -> int:
    total = 0
    for shift in P9:
        total += CRAZY[(y // shift) % 9][(x // shift) % 9] * shift
    return total


def loader_cells(source: bytes) -> list[int]:
    cells: list[int] = []
    for offset, byte in enumerate(source):
        if chr(byte).isspace():
            continue
        if not (33 <= byte <= 126):
            raise ValueError(f"non-printable source byte 0x{byte:02x} at offset {offset}")
        instruction = XLAT1[(byte - 33 + len(cells)) % 94]
        if instruction not in VALID:
            raise ValueError(
                f"cell {len(cells)} decodes to {instruction!r}; strict loader rejects it"
            )
        cells.append(byte)
        if len(cells) > MEM_SIZE:
            raise ValueError("source has more than 59049 cells")
    if len(cells) < 2:
        raise ValueError("source needs at least two cells")
    while len(cells) < MEM_SIZE:
        cells.append(crazy(cells[-1], cells[-2]))
    return cells


def run(memory: list[int], payload: bytes, max_steps: int, warmup: int = 1000) -> dict:
    mem = memory.copy()
    a = c = d = 0
    out = bytearray()
    pending = list(payload) + [None]
    seen: dict[tuple[int, int, int], tuple[int, bytes, int]] = {}
    steps = 0

    while steps < max_steps:
        if not (33 <= mem[c] <= 126):
            return {"status": "STALL", "steps": steps, "c": c, "value": mem[c], "output": bytes(out)}
        instruction = XLAT1[(mem[c] - 33 + c) % 94]
        if instruction == "j":
            d = mem[d]
        elif instruction == "i":
            c = mem[d]
        elif instruction == "*":
            a = mem[d] = mem[d] // 3 + mem[d] % 3 * 19683
        elif instruction == "p":
            a = mem[d] = crazy(a, mem[d])
        elif instruction == "<":
            out.append(a & 255)
        elif instruction == "/":
            value = pending.pop(0)
            a = 59048 if value is None else value
        elif instruction == "v":
            return {"status": "HALT", "steps": steps, "output": bytes(out)}

        mem[c] = ord(XLAT2[mem[c] - 33])
        c = (c + 1) % MEM_SIZE
        d = (d + 1) % MEM_SIZE
        steps += 1

        if steps >= warmup:
            key = (a, c, d)
            previous = seen.get(key)
            if previous is not None and previous[1] == bytes(memory_view(mem)):
                start_step, _, previous_outputs = previous
                return {
                    "status": "CYCLE",
                    "steps": steps,
                    "cycle_start": start_step,
                    "cycle_end": steps,
                    "period": steps - start_step,
                    "outputs_per_cycle": len(out) - previous_outputs,
                    "output": bytes(out),
                    "state_sha256": hashlib.sha256(
                        b"".join(cell.to_bytes(2, "little") for cell in mem)
                    ).hexdigest(),
                    "a": a,
                    "c": c,
                    "d": d,
                }
            if previous is None:
                if len(seen) >= 20000:
                    return {"status": "OUT_OF_MEMORY", "steps": steps, "output": bytes(out)}
                seen[key] = (steps, bytes(memory_view(mem)), len(out))

    return {"status": "MAX_STEPS", "steps": steps, "output": bytes(out)}


def memory_view(mem: list[int]) -> bytearray:
    return bytearray(b"".join(cell.to_bytes(2, "little") for cell in mem))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("program", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-steps", type=int, default=2_000_000)
    args = parser.parse_args()

    source = args.program.read_bytes()
    try:
        memory = loader_cells(source)
        loader = "ACCEPT"
    except ValueError as error:
        print(f"LOADER_REJECT: {error}", file=sys.stderr)
        return 1

    zero = run(memory, b"0", args.max_steps)
    one = run(memory, b"1", args.max_steps)

    checks = {
        "loader_accepts_source": loader == "ACCEPT",
        "zero_halts": zero["status"] == "HALT",
        "zero_prints_exactly_one_zero": zero.get("output") == b"0",
        "one_repeats_full_state": one["status"] == "CYCLE",
        "one_outputs_only_ones": one.get("output", b"")[:1] == b"1" and set(one["output"][1:]) == {0x31},
        "one_emits_per_cycle": one["status"] == "CYCLE" and one.get("period", 0) > 0 and one.get("outputs_per_cycle", 0) > 0,
    }

    report = {
        "program": str(args.program),
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "source_bytes": len(source),
        "loader": loader,
        "branch_zero": {
            "status": zero["status"],
            "steps": zero["steps"],
            "output_hex": zero["output"].hex(),
        },
        "branch_one": {
            "status": one["status"],
            "steps": one["steps"],
            "cycle_start": one.get("cycle_start"),
            "cycle_end": one.get("cycle_end"),
            "period": one.get("period"),
            "outputs_per_cycle": one.get("outputs_per_cycle"),
            "output_bytes": len(one.get("output", b"")),
            "first_output_hex": one.get("output", b"")[:1].hex(),
            "state_sha256": one.get("state_sha256"),
        },
        "checks": checks,
        "verdict": "DEMONSTRATED" if all(checks.values()) else "NOT_DEMONSTRATED",
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(report, indent=2))
    return 0 if report["verdict"] == "DEMONSTRATED" else 1


if __name__ == "__main__":
    sys.exit(main())
