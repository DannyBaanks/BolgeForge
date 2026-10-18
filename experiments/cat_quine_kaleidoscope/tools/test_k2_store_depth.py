#!/usr/bin/env python3
"""K2 store-depth gate: how many read/store cycles a CAT echo actually needs.

Stage E killed the *digit-wise* witness gate, but the print condition is weaker
than the digit condition: the machine emits `a & 255`, so a stored cell only has
to land in the right residue class. This suite measures that gate exactly over
all 59,049 possible cell values and reports the minimum number of `/`+`p`
cycles needed to print an arbitrary byte, then censuses the candidate's own
image against it.

Run from any directory: python3 -B <this-file> [--evidence NEW_DIRECTORY].
Requires a C compiler. Evidence directories are created exclusively; nothing
that already exists is overwritten.

Recorded paths are relative to the repository root; temporary build paths are
reduced to <tmp>/<basename>. No workstation path reaches any evidence file.
"""
import argparse
import contextlib
import hashlib
import io
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
EXPERIMENT = TOOLS.parent
ROOT = EXPERIMENT.parents[1]
WORK = EXPERIMENT / "work"
sys.path[:0] = [str(WORK), str(TOOLS), str(ROOT)]

import selector_dev
from constants import crazy_op, rot_op

N = 59049
EOF = N - 1
ALL = (1 << 256) - 1
IMAGE_CELLS = 52828
MIRROR = 26414
INPUTS = tuple(range(256)) + (EOF,)      # `/` loads a raw byte, or 59048 at EOF
BASELINE = WORK / "candidate_selector_m281.mal"
ORACLE_C = (("mb_ref", ROOT / "oracle" / "mb_ref.c"), ("trace_loop", TOOLS / "trace_loop.c"))
OUT_EXPR = "(a & 255)"
STORE_EXPR = "op(a, mem[d])"
EOF_EXPR = "(in_ch == EOF) ? 59048"
BYTE_Q, BYTE_C, BYTE_MOD32 = 81, 67, 113  # 113 == 81 (mod 32): 5-bit truncation control
Q_OUTPUT_BYTES = 53562
BRANCH_AT = 25531
LOOP_ENTRY = 25976


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def readables(v):
    """Cell values left by one `/`+`p` cycle starting from cell value v."""
    return {crazy_op(a, v) for a in INPUTS}


def printables(v):
    """Output bytes reachable right after one cycle: `p` prints its result, `*` rotates it."""
    mask = 0
    for x in readables(v):
        mask |= 1 << (x & 255)
        mask |= 1 << (rot_op(x) & 255)
    return mask


def cover(mask):
    return bin(mask).count("1")


class K2StoreDepthTests(unittest.TestCase):
    evidence = None

    @classmethod
    def setUpClass(cls):
        cc = shutil.which("cc")
        if cc is None:
            raise RuntimeError("oracle parity requires cc")
        tmp = tempfile.TemporaryDirectory(prefix="bolgeforge-store-depth-")
        cls.addClassCleanup(tmp.cleanup)
        cls.temporary = Path(tmp.name)
        cls.source_bytes = BASELINE.read_bytes()
        cls.T = [b for b in cls.source_bytes if 33 <= b <= 126]
        if len(cls.T) != IMAGE_CELLS:
            raise RuntimeError(f"unexpected clean cell count {len(cls.T)}")
        cls.binaries = {}
        for name, c_source in ORACLE_C:
            binary = cls.temporary / name
            subprocess.run([cc, "-O2", str(c_source), "-o", str(binary)],
                           check=True, capture_output=True)
            cls.binaries[name] = binary
        cls.binary_sha256 = {f"<tmp>/{name}": sha256_bytes(binary.read_bytes())
                             for name, binary in cls.binaries.items()}
        started = time.monotonic()
        after_one = [printables(v) for v in range(N)]
        after_two = [0] * N
        for v in range(N):
            mask = 0
            for x in readables(v):
                mask |= after_one[x]
            after_two[v] = mask
        after_three = [0] * N
        for v in range(N):
            mask = after_two[v]
            if mask != ALL:
                for x in readables(v):
                    for y in readables(x):
                        mask |= after_one[y]
                        if mask == ALL:
                            break
                    if mask == ALL:
                        break
            after_three[v] = mask
        cls.algebra_seconds = round(time.monotonic() - started, 2)
        cls.after_one, cls.after_two, cls.after_three = after_one, after_two, after_three
        cls.complete_at_one = [v for v in range(N) if after_one[v] == ALL]
        cls.complete_at_two = sum(1 for v in range(N) if after_two[v] == ALL)
        cls.short_at_three = [v for v in range(N) if after_three[v] != ALL]
        # census of the candidate's own image against those classes
        mem = selector_dev.pad(cls.T)
        census = {1: 0, 2: 0, 3: 0}
        distinct = sorted({mem[c] for c in range(IMAGE_CELLS)})
        for c in range(IMAGE_CELLS):
            v = mem[c]
            if after_one[v] == ALL:
                census[1] += 1
            elif after_two[v] == ALL:
                census[2] += 1
            else:
                census[3] += 1
        cls.image_census = census
        cls.image_distinct = {
            "values": len(distinct),
            "complete_at_one": sum(1 for v in distinct if after_one[v] == ALL),
            "complete_at_two": sum(1 for v in distinct
                                   if after_one[v] != ALL and after_two[v] == ALL),
            "need_three": sum(1 for v in distinct if after_two[v] != ALL),
        }

    @staticmethod
    def shown(path):
        try:
            return str(Path(path).relative_to(ROOT))
        except ValueError:
            return f"<tmp>/{Path(path).name}"

    def engine(self, name, byte, max_steps="200000000", to_file=None):
        argv = [str(self.binaries[name]), str(BASELINE), max_steps]
        if to_file is not None:
            argv += ["-o", str(to_file)]
        proc = subprocess.run(argv, input=bytes([byte]), capture_output=True,
                              timeout=300, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode(errors="replace"))
        if to_file is not None:
            return to_file.read_bytes()
        return proc.stdout

    def test_print_operand_is_the_accumulator_in_both_engines(self):
        """`<` emits `a & 255`: an echo only has to hit the right residue class."""
        for name, source in ORACLE_C:
            text = source.read_text(encoding="utf-8")
            self.assertIn(OUT_EXPR, text, name)
            self.assertIn(STORE_EXPR, text, name)

    def test_input_domain_is_a_raw_byte_or_eof_in_both_engines(self):
        for name, source in ORACLE_C:
            self.assertIn(EOF_EXPR, source.read_text(encoding="utf-8"), name)

    def test_psi_is_the_eof_read_store_and_an_involution(self):
        """An EOF read followed by a store applies psi = op(59048, .) to the cell."""
        for v in range(N):
            self.assertEqual(crazy_op(EOF, v), selector_dev.crazy_op(EOF, v), v)
        for v in (0, 1, 8, 74, 124, 526, 20173, 29524, 58830, EOF):
            self.assertEqual(crazy_op(EOF, crazy_op(EOF, v)), v, v)

    def test_one_cycle_never_suffices_for_the_candidates_own_image(self):
        self.assertEqual(self.image_census[1], 0)
        self.assertEqual(self.image_distinct["complete_at_one"], 0)
        type(self).census = {"image_cells": IMAGE_CELLS,
                             "cells_by_minimum_cycles": self.image_census,
                             "distinct_image_values": self.image_distinct}

    def test_exactly_148_cell_values_are_complete_after_one_cycle(self):
        self.assertEqual(len(self.complete_at_one), 148)
        type(self).single_cycle_set = {
            "count": len(self.complete_at_one),
            "lowest": self.complete_at_one[0],
            "highest": self.complete_at_one[-1],
            "first_16": self.complete_at_one[:16],
            "present_in_candidate_image": self.image_distinct["complete_at_one"],
        }

    def test_two_cycles_are_enough_for_40646_cell_values(self):
        self.assertEqual(self.complete_at_two, 40646)
        type(self).depth_two = {"complete": self.complete_at_two, "of": N}

    def test_three_cycles_are_enough_for_every_cell_value(self):
        self.assertEqual(self.short_at_three, [])
        type(self).depth_three = {"complete": N - len(self.short_at_three), "of": N,
                                  "short": len(self.short_at_three)}

    def test_explicit_three_cycle_witnesses_close_the_worst_gap(self):
        worst = min(range(N), key=lambda v: cover(self.after_two[v]))
        missing = [b for b in range(256) if not (self.after_two[worst] >> b) & 1]
        targets, found = set(missing), {}
        for x in readables(worst):
            if len(found) == len(targets):
                break
            for y in readables(x):
                if len(found) == len(targets):
                    break
                for z in readables(y):
                    for rotations in (0, 1):
                        value = z if rotations == 0 else rot_op(z)
                        if (value & 255) in targets and (value & 255) not in found:
                            found[value & 255] = (x, y, z, rotations)
                    if len(found) == len(targets):
                        break
        self.assertEqual(len(found), len(targets), (worst, len(targets) - len(found)))
        type(self).gap_witness = {
            "worst_cell_value": worst,
            "bytes_covered_after_two_cycles": cover(self.after_two[worst]),
            "bytes_missing_after_two_cycles": len(missing),
            "missing_bytes": missing,
            "witnesses": {str(b): list(found[b]) for b in sorted(found)},
            "witness_reading": ("cell -> op(a1,cell) -> op(a2,.) -> op(a3,.), then `*` "
                                "iff rotations=1; a_i is a stdin byte or 59048"),
        }

    def test_byte_routing_matches_across_model_and_both_oracles(self):
        mem = selector_dev.pad(self.T)
        model = {}
        for byte, expect_c in ((BYTE_Q, LOOP_ENTRY), (BYTE_C, None), (BYTE_MOD32, None)):
            state = selector_dev.sim(mem, bytes([byte]), max_steps=BRANCH_AT + 1)
            model[byte] = "Q" if state["c"] == expect_c else "not-Q"
        oracle = {}
        for byte in model:
            out = self.engine("mb_ref", byte)
            self.assertIn(len(out), (0, Q_OUTPUT_BYTES), byte)
            oracle[byte] = "Q" if len(out) == Q_OUTPUT_BYTES else "not-Q"
        self.assertEqual(model, oracle)
        self.assertEqual(oracle[BYTE_Q], "Q")
        self.assertEqual(oracle[BYTE_C], "not-Q")
        self.assertEqual(oracle[BYTE_MOD32], "not-Q")     # a 5-bit input would print here
        with tempfile.NamedTemporaryFile(dir=self.temporary, suffix=".out") as handle:
            traced = Path(handle.name)
            cross = self.engine("trace_loop", BYTE_Q, "70000000", to_file=traced)
        self.assertEqual(sha256_bytes(cross), sha256_bytes(self.engine("mb_ref", BYTE_Q)))
        type(self).byte_routing = {
            "model": {str(k): v for k, v in model.items()},
            "mb_ref": {str(k): v for k, v in oracle.items()},
            "mod32_pair": [BYTE_Q, BYTE_MOD32],
            "q_output_bytes": Q_OUTPUT_BYTES,
            "trace_loop_matches_mb_ref_on_byte_Q": True,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    if args.evidence is not None and args.evidence.exists():
        parser.error(f"evidence directory already exists: {args.evidence}")
    if args.evidence is not None:
        args.evidence.mkdir(parents=True)
    started = time.monotonic()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(K2StoreDepthTests)
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        result = unittest.TextTestRunner(stream=captured, verbosity=2).run(suite)
    text = captured.getvalue()
    print(text, end="")
    if args.evidence is not None:
        (args.evidence / "verification.txt").write_text(text, encoding="utf-8")
        data = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "cwd": ".",
            "path_recording": ("repo-relative; temporary build paths reduced to "
                               "<tmp>/<basename>"),
            "environment": {"platform": platform.platform(), "python": sys.version},
            "exit_status": 0 if result.wasSuccessful() else 1,
            "tests": result.testsRun, "failures": len(result.failures),
            "errors": len(result.errors), "elapsed_seconds": time.monotonic() - started,
            "algebra_seconds": K2StoreDepthTests.algebra_seconds,
            "inputs_sha256": {
                str(BASELINE.relative_to(ROOT)): sha256_bytes(BASELINE.read_bytes()),
                str((ROOT / "oracle" / "mb_ref.c").relative_to(ROOT)):
                    sha256_bytes((ROOT / "oracle" / "mb_ref.c").read_bytes()),
                str((TOOLS / "trace_loop.c").relative_to(ROOT)):
                    sha256_bytes((TOOLS / "trace_loop.c").read_bytes()),
                str(Path(__file__).resolve().relative_to(ROOT)):
                    sha256_bytes(Path(__file__).read_bytes()),
            },
            "oracle_binaries_sha256": K2StoreDepthTests.binary_sha256,
            "print_semantics": {
                "output_operand": OUT_EXPR, "store_operand": STORE_EXPR,
                "input_operand": "a := raw byte 0..255, 59048 at EOF",
                "sources": [str(path.relative_to(ROOT)) for _, path in ORACLE_C],
            },
            "input_domain": {"readable_a_values": "0..255 plus 59048 at EOF",
                             "count": len(INPUTS)},
            "depth1_complete_cell_values": getattr(K2StoreDepthTests, "single_cycle_set", None),
            "depth2": getattr(K2StoreDepthTests, "depth_two", None),
            "depth3": getattr(K2StoreDepthTests, "depth_three", None),
            "candidate_image_census": getattr(K2StoreDepthTests, "census", None),
            "worst_gap_witness": getattr(K2StoreDepthTests, "gap_witness", None),
            "byte_routing_parity": getattr(K2StoreDepthTests, "byte_routing", None),
            "claims": {
                "`<` prints a & 255 and `/` loads a raw byte in both engines": "DEMONSTRATED",
                "psi = op(59048, .) is the EOF-read-plus-store action, an involution":
                    "DEMONSTRATED",
                "exactly 148 cell values can print every byte after ONE read/store cycle":
                    "DEMONSTRATED",
                "no cell value present in the candidate image is in that 148-value set":
                    "DEMONSTRATED",
                "two read/store cycles suffice for 40,646 of the 59,049 cell values":
                    "DEMONSTRATED",
                "three read/store cycles suffice for every cell value (0 short)":
                    "DEMONSTRATED",
                "the worst two-cycle gap is closed with explicit three-cycle witnesses":
                    "DEMONSTRATED",
                "model, mb_ref and trace_loop agree on which input byte takes which branch":
                    "DEMONSTRATED",
                "an executable C-branch read/store loop": "NOT_DEMONSTRATED",
                "C echoes stdin bytes (CAT row)": "NOT_DEMONSTRATED",
                "single program satisfying both QUINE and CAT rows (K2)": "NOT_DEMONSTRATED",
            },
            "not_demonstrated": [
                "rail machinery for 2-3 chained `/`+`p` cycles onto one chosen cell",
                "that the print loop can be re-entered after each cycle",
                "payload echo in the C branch", "executable K2",
                "self-modifying stability across a read/store loop"],
        }
        (args.evidence / "results.json").write_text(json.dumps(data, indent=2) + "\n",
                                                   encoding="utf-8")
        hashes = {path.name: sha256_bytes(path.read_bytes())
                  for path in args.evidence.iterdir() if path.is_file()}
        (args.evidence / "hashes.json").write_text(json.dumps(hashes, indent=2) + "\n",
                                                   encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
