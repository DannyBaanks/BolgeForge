#!/usr/bin/env python3
"""Synthesize a strict-valid variant of the 90-byte Classic Truth Machine.

This is a behavior-preserving variant synthesizer, not an independent
from-scratch design. It traces the reference for inputs 0 and 1, finds cells
that are never read or written, re-encodes those cells with different valid
opcodes, and verifies the result with the strict loader and cycle prover.

Usage:
  python3 tools/synthesize_truth_machine_variant.py
  python3 tools/synthesize_truth_machine_variant.py --seed PATH --out PATH
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def rel(path: Path) -> str:
    """Repo-relative path for evidence records; no workstation-specific paths."""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()

from constants import MEM_SIZE, XLAT1, XLAT2, crazy_op

DEFAULT_SEED = REPO_ROOT / "artifacts/truth_machine_classic_90b.mal"
DEFAULT_OUT = REPO_ROOT / "artifacts/truth_machine_variant_90b.mal"
DEFAULT_EVIDENCE = REPO_ROOT / "docs/evidence/2026-10-22-truth-machine-variant"
PROVER = REPO_ROOT / "tools/prove_truth_machine.py"
MB_REF = REPO_ROOT / "mb_ref"
OPS = "ji*p</vo"
VALID = frozenset(OPS)


def decode(byte: int, address: int) -> str:
    return XLAT1[(byte - 33 + address) % 94]


def encode(op: str, address: int) -> int:
    return ((XLAT1.index(op) - (address % 94)) % 94) + 33


def strict_cells(source: bytes) -> list[int]:
    cells: list[int] = []
    for offset, byte in enumerate(source):
        if chr(byte).isspace():
            continue
        if not (33 <= byte <= 126):
            raise ValueError(f"non-printable source byte 0x{byte:02x} at offset {offset}")
        op = decode(byte, len(cells))
        if op not in VALID:
            raise ValueError(f"cell {len(cells)} decodes to {op!r}")
        cells.append(byte)
    if len(cells) < 2:
        raise ValueError("source needs at least two cells")
    if len(cells) > MEM_SIZE:
        raise ValueError("source has more than 59049 cells")
    return cells


def initial_memory(cells: list[int]) -> list[int]:
    memory = cells + [0] * (MEM_SIZE - len(cells))
    for address in range(len(cells), MEM_SIZE):
        memory[address] = crazy_op(memory[address - 1], memory[address - 2])
    return memory


def trace(memory: list[int], payload: bytes, max_steps: int) -> dict:
    mem = memory.copy()
    a = c = d = 0
    pending = list(payload) + [None]
    output = bytearray()
    reads: set[int] = set()
    writes: set[int] = set()
    seen: dict[tuple, int] = {}
    cycle_start = None

    for step in range(max_steps):
        reads.add(c)
        reads.add(d)
        byte = mem[c]
        if not (33 <= byte <= 126):
            return {
                "status": "INVALID_EXECUTION",
                "steps": step,
                "address": c,
                "cell": byte,
                "output": bytes(output),
                "reads": reads,
                "writes": writes,
            }
        op = decode(byte, c)
        if op == "j":
            d = mem[d]
        elif op == "i":
            c = mem[d]
        elif op == "*":
            mem[d] = mem[d] // 3 + mem[d] % 3 * 19683
            a = mem[d]
            writes.add(d)
        elif op == "p":
            mem[d] = crazy_op(a, mem[d])
            a = mem[d]
            writes.add(d)
        elif op == "<":
            output.append(a & 255)
        elif op == "/":
            value = pending.pop(0)
            a = 59048 if value is None else value
        elif op == "v":
            return {
                "status": "HALT",
                "steps": step,
                "output": bytes(output),
                "reads": reads,
                "writes": writes,
            }

        next_byte = mem[c]
        if not (33 <= next_byte <= 126):
            return {
                "status": "INVALID_EXECUTION",
                "steps": step,
                "address": c,
                "cell": next_byte,
                "output": bytes(output),
                "reads": reads,
                "writes": writes,
            }
        mem[c] = ord(XLAT2[next_byte - 33])
        c = (c + 1) % MEM_SIZE
        d = (d + 1) % MEM_SIZE

        key = (a, c, d, tuple(mem[:200]))
        if step > 500 and key in seen:
            cycle_start = seen[key]
            return {
                "status": "CYCLE",
                "steps": step,
                "period": step - cycle_start,
                "output": bytes(output),
                "reads": reads,
                "writes": writes,
                "state_sha256": hashlib.sha256(
                    b"".join(cell.to_bytes(2, "little") for cell in mem)
                ).hexdigest(),
            }
        seen.setdefault(key, step)

    return {
        "status": "MAX_STEPS",
        "steps": max_steps,
        "output": bytes(output),
        "reads": reads,
        "writes": writes,
    }


def free_cells(cells: list[int], zero: dict, one: dict) -> list[int]:
    touched = zero["reads"] | zero["writes"] | one["reads"] | one["writes"]
    return [address for address in range(len(cells)) if address not in touched]


def next_encoding(byte: int, address: int) -> tuple[str, int, str]:
    old_op = decode(byte, address)
    for offset in range(1, len(OPS) + 1):
        new_op = OPS[(OPS.index(old_op) + offset) % len(OPS)]
        new_byte = encode(new_op, address)
        if new_byte != byte:
            return old_op, new_op, new_byte
    raise ValueError(f"no alternative encoding at cell {address}")


def read_cell_control(source: bytes, cells: list[int], address: int) -> dict:
    old_op, new_op, new_byte = next_encoding(cells[address], address)
    mutant = bytearray(source)
    mutant[address] = new_byte
    record = {
        "address": address,
        "old_op": old_op,
        "new_op": new_op,
    }
    try:
        mutant_cells = strict_cells(bytes(mutant))
    except ValueError as exc:
        return {
            **record,
            "strict_loader": "REJECT",
            "reason": str(exc),
            "verdict": "NOT_DEMONSTRATED",
        }
    result = verify(initial_memory(mutant_cells))
    return {
        **record,
        "strict_loader": "ACCEPT",
        "zero_status": result["zero"]["status"],
        "one_status": result["one"]["status"],
        "verdict": result["verdict"],
    }


def public_run(result: dict) -> dict:
    output = result.get("output", b"")
    return {
        **{k: v for k, v in result.items() if k not in ("reads", "writes", "output")},
        "output_hex": output.hex(),
        "output_len": len(output),
    }


def verify(memory: list[int]) -> dict:
    zero = trace(memory, b"0", 3000)
    one = trace(memory, b"1", 3000)
    checks = {
        "zero_halts": zero["status"] == "HALT",
        "zero_prints_one_zero": zero.get("output") == b"0",
        "one_cycles": one["status"] == "CYCLE",
        "one_period_positive": one.get("period", 0) > 0,
        "one_outputs_ones": bool(one.get("output")) and set(one["output"]) == {0x31},
    }
    return {
        "checks": checks,
        "zero": public_run(zero),
        "one": public_run(one),
        "verdict": "DEMONSTRATED" if all(checks.values()) else "NOT_DEMONSTRATED",
    }


def run_json(command: list[str], stdin: bytes = b"") -> dict:
    result = subprocess.run(
        command,
        input=stdin.decode("utf-8") if stdin else None,
        capture_output=True,
        text=True,
        timeout=300,
        cwd=REPO_ROOT,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"stdout": result.stdout, "stderr": result.stderr}
    return {
        "command": command,
        "returncode": result.returncode,
        "stderr": result.stderr,
        "payload": payload,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE)
    args = parser.parse_args()

    seed_source = args.seed.read_bytes()
    seed_cells = strict_cells(seed_source)
    seed_memory = initial_memory(seed_cells)
    seed_zero = trace(seed_memory, b"0", 3000)
    seed_one = trace(seed_memory, b"1", 3000)
    seed_check = verify(seed_memory)
    if seed_check["verdict"] != "DEMONSTRATED":
        print(f"seed does not satisfy the truth-machine specification: {seed_check}", file=sys.stderr)
        return 1

    free = free_cells(seed_cells, seed_zero, seed_one)
    if not free:
        print("no free cells found", file=sys.stderr)
        return 1

    candidate = bytearray(seed_source)
    changes = []
    for address in free:
        old_op, new_op, new_byte = next_encoding(candidate[address], address)
        changes.append(
            {
                "address": address,
                "old_byte": candidate[address],
                "new_byte": new_byte,
                "old_op": old_op,
                "new_op": new_op,
            }
        )
        candidate[address] = new_byte

    candidate_source = bytes(candidate)
    candidate_cells = strict_cells(candidate_source)
    candidate_memory = initial_memory(candidate_cells)
    candidate_check = verify(candidate_memory)
    if candidate_check["verdict"] != "DEMONSTRATED":
        print(f"variant failed verification: {candidate_check}", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(candidate_source)

    prover = run_json(["python3", rel(PROVER), rel(args.out), "--json"])
    mb_ref_zero = None
    mb_ref_one = None
    if MB_REF.exists():
        zero_run = subprocess.run(
            [str(MB_REF), str(args.out), "10000"],
            input=b"0",
            capture_output=True,
            timeout=120,
        )
        one_run = subprocess.run(
            [str(MB_REF), str(args.out), "1408"],
            input=b"1",
            capture_output=True,
            timeout=120,
        )
        mb_ref_zero = {
            "returncode": zero_run.returncode,
            "stdout_hex": zero_run.stdout.hex(),
            "stderr": zero_run.stderr.decode("utf-8", "replace"),
        }
        mb_ref_one = {
            "returncode": one_run.returncode,
            "stdout_len": len(one_run.stdout),
            "stdout_all_ones": bool(one_run.stdout) and set(one_run.stdout) == {0x31},
            "stderr": one_run.stderr.decode("utf-8", "replace"),
        }

    control_addresses = [a for a in (0, 37, 41, 73) if a < len(candidate_cells)]
    controls = [read_cell_control(candidate_source, candidate_cells, a) for a in control_addresses]

    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": (
            "Behavior-preserving strict-valid variant of the 90-byte CC BY-SA 4.0 "
            "reference. This is not an independent from-scratch synthesis; "
            "independent architecture synthesis remains OPEN."
        ),
        "seed": {
            "path": rel(args.seed),
            "bytes": len(seed_source),
            "sha256": hashlib.sha256(seed_source).hexdigest(),
            "free_cells": free,
        },
        "variant": {
            "path": rel(args.out),
            "bytes": len(candidate_source),
            "sha256": hashlib.sha256(candidate_source).hexdigest(),
            "changes": changes,
        },
        "verification": {
            "strict_loader": "ACCEPT",
            "local": candidate_check,
            "prover": prover,
            "mb_ref_zero": mb_ref_zero,
            "mb_ref_one": mb_ref_one,
            "controls": controls,
        },
    }

    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.evidence_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.evidence_dir / "candidate.mal").write_bytes(candidate_source)
    sums = [
        f"{report['variant']['sha256']}  {rel(args.out)}",
        f"{hashlib.sha256(report_path.read_bytes()).hexdigest()}  {rel(report_path)}",
    ]
    report_md = args.evidence_dir / "REPORT.md"
    if report_md.exists():
        sums.append(f"{hashlib.sha256(report_md.read_bytes()).hexdigest()}  {rel(report_md)}")
    (args.evidence_dir / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")
    (args.evidence_dir / "commands.txt").write_text(
        "python3 tools/synthesize_truth_machine_variant.py\n"
        f"python3 tools/prove_truth_machine.py {rel(args.out)} --json\n",
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
