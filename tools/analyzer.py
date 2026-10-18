#!/usr/bin/env python3
"""tools/analyzer.py - BolgeForge Program Analyzer & Target Extractor.

Analyzes any Classic Malbolge program (such as Lutter's malbolge.org corpus),
identifies the initialization preamble, extracts target memory variables,
characterizes the core loop, and computes resynthesis potential under
BolgeForge's Dijkstra synthesizer.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Add repo root to import constants
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from constants import rot_op, crazy_op, XLAT1, XLAT2, MEM_SIZE


def analyze_program(path: Path, max_preamble_steps: int = 100000) -> dict:
    raw = path.read_bytes()
    clean = [b for b in raw if 33 <= b <= 126]
    total_file_bytes = len(raw)
    total_prog_chars = len(clean)

    # Initialize memory according to Olmstead specification
    mem = list(clean) + [0] * (MEM_SIZE - total_prog_chars)
    for i in range(total_prog_chars, MEM_SIZE):
        mem[i] = crazy_op(mem[i - 1], mem[i - 2])

    init_mem = list(mem)

    a = c = d = step = 0
    first_io_step = None
    first_io_type = None

    t0 = time.time()
    while step < max_preamble_steps:
        instr = mem[c]
        idx = (instr - 33 + c) % 94 if 33 <= instr <= 126 else 0
        ch = XLAT1[idx]

        if ch in ('/', '<') and first_io_step is None:
            first_io_step = step
            first_io_type = 'input (/)' if ch == '/' else 'output (<)'
            break

        if ch == 'j':
            d = mem[d]
        elif ch == 'i':
            c = mem[d]
        elif ch == '*':
            mem[d] = rot_op(mem[d])
            a = mem[d]
        elif ch == 'p':
            mem[d] = crazy_op(a, mem[d])
            a = mem[d]
        elif ch == 'v':
            break

        if 33 <= mem[c] <= 126:
            mem[c] = ord(XLAT2[mem[c] - 33])

        c = 0 if c == 59048 else c + 1
        d = 0 if d == 59048 else d + 1
        step += 1

    elapsed = time.time() - t0

    # Identify modified memory cells in data/high memory
    high_mod = {i: mem[i] for i in range(total_prog_chars, MEM_SIZE) if mem[i] != init_mem[i]}
    preamble_steps = first_io_step if first_io_step is not None else step

    # Estimation of BolgeForge re-synthesis cost:
    # Prefix: ~1,473 ops
    # High variables: mean ~42 ops per variable under 26-edge Dijkstra graph
    # Margin / jumps / loop slice
    bf_est_synth_ops = 1473 + int(len(high_mod) * 42.5)
    bf_est_bytes = int((bf_est_synth_ops + (total_prog_chars - c)) * 1.015)

    res = {
        "file": str(path.name),
        "total_file_bytes": total_file_bytes,
        "total_prog_chars": total_prog_chars,
        "preamble_steps": preamble_steps,
        "first_io_type": first_io_type,
        "handoff_state": {"step": preamble_steps, "c": c, "d": d, "a": a},
        "high_memory_variables_count": len(high_mod),
        "variable_address_range": [min(high_mod.keys()), max(high_mod.keys())] if high_mod else [],
        "analysis_time_seconds": round(elapsed, 4),
        "bolgeforge_synthesis_potential": {
            "target_variables": len(high_mod),
            "estimated_synth_ops": bf_est_synth_ops,
            "estimated_compact_file_bytes": bf_est_bytes,
            "estimated_reduction_percentage": round(max(0, (1.0 - (bf_est_bytes / total_file_bytes)) * 100), 1),
        },
        "targets": high_mod,
    }
    return res


def main():
    parser = argparse.ArgumentParser(description="BolgeForge Malbolge Program Analyzer")
    parser.add_argument("file", type=Path, help="Path to Malbolge (.mal / .mb) file")
    parser.add_argument("--export-targets", type=Path, help="Export extracted targets as JSON")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: {args.file} not found", file=sys.stderr)
        sys.exit(1)

    data = analyze_program(args.file)

    print("=" * 60)
    print(f"BOLGEFORGE PROGRAM ANALYSIS: {data['file']}")
    print("=" * 60)
    print(f"Total File Size:       {data['total_file_bytes']:,} bytes ({data['total_prog_chars']:,} instructions)")
    print(f"Preamble Steps:        {data['preamble_steps']:,} steps before {data['first_io_type']}")
    print(f"Handoff State:         c = {data['handoff_state']['c']}, d = {data['handoff_state']['d']}, a = {data['handoff_state']['a']}")
    print(f"Target Variables:      {data['high_memory_variables_count']} cells in memory range {data['variable_address_range']}")
    print("-" * 60)
    pot = data['bolgeforge_synthesis_potential']
    print(f"BolgeForge Resynthesis Potential:")
    print(f"  Estimated Synth Ops: {pot['estimated_synth_ops']:,}")
    print(f"  Estimated File Size: {pot['estimated_compact_file_bytes']:,} bytes")
    print(f"  Projected Reduction: -{data['total_file_bytes'] - pot['estimated_compact_file_bytes']:,} bytes ({pot['estimated_reduction_percentage']}%)")
    print("=" * 60)

    if args.export_targets:
        args.export_targets.write_text(json.dumps(data, indent=2))
        print(f"Exported full targets to {args.export_targets}")


if __name__ == '__main__':
    main()
