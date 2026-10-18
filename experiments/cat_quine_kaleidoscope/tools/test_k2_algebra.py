#!/usr/bin/env python3
"""Regression controls for K2 algebra, not a claim of an executable CAT.

Run from any directory: python3 -B <this-file> [--evidence NEW_DIRECTORY].
Requires a C compiler. Evidence directories are created exclusively; no old
reports, candidate sources or reachability caches are overwritten.
"""
import argparse
import contextlib
import ctypes
import hashlib
import io
import json
import pickle
import platform
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone

TOOLS = Path(__file__).resolve().parent
EXPERIMENT = TOOLS.parent
ROOT = EXPERIMENT.parents[1]
WORK = EXPERIMENT / "work"
sys.path[:0] = [str(WORK), str(TOOLS), str(ROOT)]

import k2_branch2 as branch
import k2_gate as gate
import k2_branch as restricted
import selector_dev
from constants import crazy_op, rot_op

N = 59049
EOF = N - 1
RESET_CONTROLS = (29524, EOF, 0)
SHIM = r'''
#define main mb_ref_main
#include "oracle/mb_ref.c"
#undef main
unsigned short k2_op(unsigned short ctrl, unsigned short cell) {
    return op(ctrl, cell);
}
void k2_pad(const unsigned short *prefix, unsigned n, unsigned short *mem) {
    unsigned i;
    for (i = 0; i < n; ++i) mem[i] = prefix[i];
    for (; i < 59049; ++i) mem[i] = op(mem[i-1], mem[i-2]);
}
'''


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    """Normalise a path for the evidence record.

    Absolute repo paths become repo-relative; absolute paths outside the
    repository (the interpreter, the per-run temporary build) are reduced to
    their basename under a fixed placeholder, so no workstation location can
    reach a published report. Relative arguments (flags, argv tokens) pass
    through unchanged. Recorded commands stay runnable with "cwd": ".".
    """
    path = Path(path)
    if not path.is_absolute():
        return str(path)
    if path == ROOT:
        return "."
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return f"<outside-repo>/{path.name}"


class K2AlgebraTests(unittest.TestCase):
    evidence = None

    @classmethod
    def setUpClass(cls):
        cc = shutil.which("cc")
        if cc is None:
            raise RuntimeError("C oracle verification requires cc")
        tmp = tempfile.TemporaryDirectory(prefix="bolgeforge-k2-")
        cls.addClassCleanup(tmp.cleanup)
        cls.temporary = Path(tmp.name)
        src, lib = Path(tmp.name) / "shim.c", Path(tmp.name) / "shim.so"
        src.write_text(SHIM, encoding="ascii")
        cls.compile_command = [cc, "-O2", "-std=c99", "-shared", "-fPIC",
                               "-I", str(ROOT), str(src), "-o", str(lib)]
        subprocess.run(cls.compile_command, check=True, capture_output=True)
        cls.compiler_version = subprocess.run(
            [cc, "--version"], check=True, capture_output=True, text=True).stdout
        cls.recorded_compile_command = [rel(cc), "-O2", "-std=c99", "-shared",
                                        "-fPIC", "-I", ".", rel(src), "-o", rel(lib)]
        cls.library_sha256 = sha256(lib)
        cls.library = ctypes.CDLL(str(lib))
        cls.library.k2_op.argtypes = [ctypes.c_ushort, ctypes.c_ushort]
        cls.library.k2_op.restype = ctypes.c_ushort
        word_pointer = ctypes.POINTER(ctypes.c_ushort)
        cls.library.k2_pad.argtypes = [word_pointer, ctypes.c_uint, word_pointer]
        cls.library.k2_pad.restype = None
        cls.c_op = staticmethod(cls.library.k2_op)
        with (WORK / "k2_reach_full.pkl").open("rb") as f:
            cls.cache = pickle.load(f)
        cls.searches = {stored: branch.search(cls.cache["depth"], stored=stored)
                        for stored in (False, True)}

    def test_eof_is_base9_eights_not_twos(self):
        for module in (branch, gate, restricted):
            self.assertEqual(module.digits(EOF), [8] * 5)
            self.assertEqual(module.from_digits([8] * 5), EOF)
            self.assertEqual(module.from_digits([2] * 5), 14762)
        f = lambda value: self.c_op(self.c_op(value, 19691), 29880)
        self.assertEqual(f(EOF), 49563)
        self.assertEqual(f(14762), 8010)
        self.assertNotEqual(f(EOF), f(14762))

    def test_legacy_search_reports_use_real_eof(self):
        for module in (gate, restricted):
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                module.main()
            rows = re.findall(
                r"K1=(\d+).*?K2=(\d+).*?A(?:\(EOF\))?=(\d+).*?B(?:\(data\))?=(\d+)",
                captured.getvalue())
            self.assertTrue(rows)
            for k1, k2, eof_class, data_class in rows:
                k1, k2, eof_class, data_class = map(int, (k1, k2, eof_class, data_class))
                self.assertEqual(self.c_op(self.c_op(EOF, k1), k2), eof_class)
                for byte in range(256):
                    self.assertEqual(self.c_op(self.c_op(byte, k1), k2), data_class)
            print(f"{module.__name__}: {len(rows)} printed gate witnesses verified with real EOF")

    def test_operator_and_orientation_against_c(self):
        for ctrl in (0, 67, 81, 19720, 29524, EOF):
            for cell in range(N):
                self.assertEqual(branch.opw(ctrl, cell), self.c_op(ctrl, cell))
        for place in branch.P9:
            for x in range(9):
                for y in range(9):
                    a, b = x * place, y * place
                    self.assertEqual(branch.opw(a, b), crazy_op(a, b))
        self.assertNotEqual(self.c_op(81, 29524), self.c_op(29524, 81))
        print("operator parity: 354294 full-word C comparisons; swapped-order control differs")

    def test_full_initial_memory_parity(self):
        for artifact in (ROOT / "artifacts/candidate_m281_53562b.mal",
                         WORK / "candidate_selector_m281.mal"):
            prefix = [b for b in artifact.read_bytes() if b not in b" \t\n\r\v\f"]
            self.assertTrue(all(33 <= b <= 126 for b in prefix))
            self.assertTrue(2 <= len(prefix) <= N)
            source = (ctypes.c_ushort * len(prefix))(*prefix)
            actual = (ctypes.c_ushort * N)()
            self.library.k2_pad(source, len(prefix), actual)
            normal, swapped = list(prefix), list(prefix)
            while len(normal) < N:
                normal.append(branch.opw(normal[-1], normal[-2]))
                swapped.append(branch.opw(swapped[-2], swapped[-1]))
            self.assertEqual(normal, list(actual))
            negative = sum(a != b for a, b in zip(swapped, actual))
            self.assertGreater(negative, 0)
            print(f"{artifact.name}: 59049 cells match C; swapped pad mismatches={negative}")

    def test_reach_cache_paths_and_closure(self):
        depth, parent = self.cache["depth"], self.cache["parent"]
        self.assertEqual(set(depth), set(parent))
        self.assertEqual(depth[19720], 0)
        self.assertIsNone(parent[19720])
        for value, edge in parent.items():
            if value == 19720:
                continue
            previous, operation = edge
            expected = (rot_op(previous) if operation == "R" else
                        self.c_op(previous, operation[1]))
            if operation != "R":
                self.assertEqual(operation[0], "P")
                self.assertIn(operation[1], range(33, 127))
            self.assertEqual(value, expected)
            self.assertEqual(depth[value], depth[previous] + 1)
        for value in depth:
            self.assertIn(rot_op(value), depth)
            for operand in range(33, 127):
                self.assertIn(self.c_op(value, operand), depth)
        print(f"reach cache: {len(depth)} witnessed values; closed under R and P(33..126)")

    def test_all_returned_candidates_against_c(self):
        for stored, (stats, hits) in self.searches.items():
            self.assertTrue(hits)
            self.assertEqual(stats["hits"], len(hits))
            classes = {(h[2], h[3], h[4], h[5]) for h in hits}
            for k1, k2, eof_class, data_class in classes:
                for byte in range(256):
                    value = self.c_op(byte, 29524) if stored else byte
                    self.assertEqual(self.c_op(self.c_op(value, k1), k2), data_class)
                value = self.c_op(EOF, 29524) if stored else EOF
                self.assertEqual(self.c_op(self.c_op(value, k1), k2), eof_class)
                self.assertNotEqual(data_class, eof_class)
            for total, cost, k1, k2, a, b, yf, td, te in hits:
                self.assertEqual(self.c_op(b, yf), td)
                self.assertEqual(self.c_op(a, yf), te)
                self.assertIn(td + 1, branch.SAFE_ZONE)
                self.assertIn(te + 1, branch.SAFE_ZONE)
                self.assertNotEqual(td, te)
                self.assertEqual(cost, self.cache["depth"][k1] + self.cache["depth"][k2])
                self.assertEqual(total, cost + self.cache["depth"][yf])
            print(f"stored={stored}: {stats}; {len(classes)} gate witnesses checked over 257 inputs")
            print(f"best stored={stored}: {hits[0]}")

    def test_optimized_search_matches_small_bruteforce(self):
        values = (29880, 13373, 6075, 25758, 6399, 7263, 46196, 45319)
        depth = {v: self.cache["depth"][v] for v in values}
        for stored in (False, True):
            gates = {}
            for k1 in values:
                for k2 in values:
                    outputs = {self.c_op(self.c_op(self.c_op(b, 29524) if stored else b,
                                                  k1), k2) for b in range(256)}
                    if len(outputs) != 1:
                        continue
                    b = outputs.pop()
                    a = self.c_op(self.c_op(self.c_op(EOF, 29524) if stored else EOF,
                                           k1), k2)
                    if a == b:
                        continue
                    item = (depth[k1] + depth[k2], k1, k2, a, b)
                    gates[a, b] = min(item, gates.get((a, b), item))
            expected = []
            for cost, k1, k2, a, b in gates.values():
                for yf in values:
                    td, te = self.c_op(b, yf), self.c_op(a, yf)
                    if td + 1 in branch.SAFE_ZONE and te + 1 in branch.SAFE_ZONE and td != te:
                        expected.append((cost + depth[yf], cost, k1, k2, a, b, yf, td, te))
            self.assertEqual(branch.search(depth, stored=stored)[1], sorted(expected))

    def test_r4_storage_and_blind_rearm(self):
        for byte in (*range(256), EOF):
            self.assertEqual(self.c_op(self.c_op(byte, 29524), 29524), byte)
        for control in RESET_CONTROLS:
            self.assertEqual(rot_op(control), control)
        for value in range(N):
            current = value
            for control in RESET_CONTROLS:
                current = self.c_op(control, current)
            self.assertEqual(current, 29524)
        print("rearm controls (29524,59048,0): all 59049 cell values -> 29524")
        print("rearm is a register-level primitive; addressing and instruction cycles not demonstrated")

    def test_selector_is_unchanged_and_original_paths_survive(self):
        source = WORK / "candidate_selector_m281.mal"
        preserved = EXPERIMENT / "evidence/M3_SELECTOR_20261018/candidate_selector_m281.mal"
        self.assertEqual(source.read_bytes(), preserved.read_bytes())
        mem = selector_dev.pad([b for b in source.read_bytes() if 33 <= b <= 126])
        q = selector_dev.sim(mem, b"Q", stop_at_loop_c=25976)
        self.assertEqual((q["reason"], q["c"], q["d"], q["a"], q["ip"], q["prints"]),
                         ("loop_entry", 25976, 26409, 26407, 1, 0))
        c = selector_dev.sim(mem, b"C")
        self.assertEqual((c["reason"], c["c"], c["ip"], c["prints"]), ("halt", 36, 1, 0))
        print("selector unchanged: Q preentry preserved; C still halts without echo")

    def test_selector_q_and_c_on_compiled_oracle(self):
        source = WORK / "candidate_selector_m281.mal"
        oracle, tracer = self.temporary / "mb_ref", self.temporary / "trace_loop"
        for c_source, binary in ((ROOT / "oracle/mb_ref.c", oracle),
                                 (TOOLS / "trace_loop.c", tracer)):
            subprocess.run([shutil.which("cc"), "-O2", str(c_source), "-o", str(binary)],
                           check=True, capture_output=True)
        type(self).vm_runs = []
        for name, feed in (("Q", b"Q"), ("C", b"C" + bytes(range(256)))):
            output = self.temporary / f"trace_{name}.bin"
            command = [str(oracle), rel(source), "70000000"]
            primary = subprocess.run(command, input=feed, capture_output=True,
                                     timeout=30, cwd=ROOT)
            trace_argv = [str(tracer), rel(source), "70000000", "-f", "25976",
                          "-w", "0", "-o", str(output)]
            trace = subprocess.run(trace_argv, input=feed, capture_output=True,
                                   timeout=30, cwd=ROOT)
            self.assertEqual(primary.returncode, 0)
            self.assertEqual(trace.returncode, 0)
            self.assertIn(b"halt=v ", trace.stdout)
            self.assertIn(b"stdin reads: preamble=1 loop=0", trace.stdout)
            self.assertEqual(output.read_bytes(), primary.stdout)
            if name == "Q":
                self.assertEqual(primary.stdout, source.read_bytes())
            else:
                self.assertEqual(primary.stdout, b"")
                self.assertNotEqual(primary.stdout, feed[1:])
            summary = next(line for line in trace.stdout.decode().splitlines()
                           if line.startswith("steps="))
            print(f"compiled C mode {name}: {summary}")
            type(self).vm_runs.append({
                "mode": name, "cwd": ".",
                "oracle_command": [rel(oracle)] + command[1:],
                "trace_command": [rel(tracer)] + trace_argv[1:-2] + ["-o", rel(output)],
                "oracle_exit": primary.returncode, "trace_exit": trace.returncode,
                "oracle_sha256": sha256(oracle), "tracer_sha256": sha256(tracer),
                "summary": summary,
            })
            if self.evidence is not None:
                for suffix, data in (("stdin.bin", feed), ("stdout.bin", primary.stdout),
                                     ("stderr.txt", primary.stderr), ("trace.txt", trace.stdout),
                                     ("trace_stderr.txt", trace.stderr)):
                    with (self.evidence / f"{name}_{suffix}").open("xb") as f:
                        f.write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, help="new, non-existing evidence directory")
    args = parser.parse_args()
    if args.evidence is not None:
        args.evidence.mkdir(parents=False, exist_ok=False)
    K2AlgebraTests.evidence = args.evidence
    started = time.monotonic()
    captured = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(K2AlgebraTests)
    with contextlib.redirect_stdout(captured):
        result = unittest.TextTestRunner(stream=captured, verbosity=2).run(suite)
    text = captured.getvalue()
    print(text, end="")
    if args.evidence is not None:
        (args.evidence / "verification.txt").write_text(text, encoding="utf-8")
        sources = [Path(__file__).resolve(), ROOT / "oracle/mb_ref.c", ROOT / "constants.py",
                   TOOLS / "trace_loop.c",
                   TOOLS / "selector_dev.py", WORK / "k2_branch.py", WORK / "k2_branch2.py",
                   WORK / "k2_gate.py", WORK / "k2_reach_full.pkl",
                   ROOT / "artifacts/candidate_m281_53562b.mal",
                   WORK / "candidate_selector_m281.mal"]
        report = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "command": [rel(a) for a in sys.orig_argv],
            "cwd": rel(Path.cwd()),
            "path_recording": ("repo-relative; out-of-repo paths (interpreter, temporary "
                               "build) reduced to <outside-repo>/<basename>"),
            "environment": {"platform": platform.platform(), "python": sys.version},
            "exit_status": 0 if result.wasSuccessful() else 1,
            "tests": result.testsRun, "failures": len(result.failures),
            "errors": len(result.errors), "skipped": len(result.skipped),
            "elapsed_seconds": time.monotonic() - started,
            "compiler": getattr(K2AlgebraTests, "compiler_version", None),
            "compile_command": getattr(K2AlgebraTests, "recorded_compile_command", None),
            "c_oracle_library_sha256": getattr(K2AlgebraTests, "library_sha256", None),
            "vm_runs": getattr(K2AlgebraTests, "vm_runs", []),
            "scope": "Algebra and unchanged-selector regression, single oracle lineage",
            "not_demonstrated": ["executable K2", "CAT payload echo", "rearm routing",
                                 "stable self-encrypting echo loop", "two-engine parity"],
            "inputs_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in sources},
            "searches": {"stored" if stored else "raw": {"stats": stats, "best": hits[0]}
                         for stored, (stats, hits) in getattr(K2AlgebraTests, "searches", {}).items()},
        }
        (args.evidence / "results.json").write_text(json.dumps(report, indent=2) + "\n",
                                                   encoding="utf-8")
        hashes = {p.name: sha256(p) for p in args.evidence.iterdir() if p.is_file()}
        (args.evidence / "hashes.json").write_text(json.dumps(hashes, indent=2) + "\n",
                                                  encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
