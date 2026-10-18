#!/usr/bin/env python3
"""K2 C-branch seam: the Q/C divergence is pure d routing, and one mirrored
byte edit re-routes the C branch into the print loop while Q stays byte-exact.

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

N = 59049
EOF = N - 1
MIRROR = 26414
CLEAN_CELLS = 52828
BASELINE = WORK / "candidate_selector_m281.mal"
BRANCH_CELL = 25646              # the shared `i` that splits the two branches
AT_BRANCH_CELL = 25531           # sim(max_steps=k) executes k instructions
BEFORE_BRANCH_CELL = 25530
AFTER_BRANCH = 25532
LOOP_ENTRY = 25976
PLANT_LC, PLANT_LQ = 40, 44      # cells holding zC and zQ
ZQ, ZC, Y = 89, 122, 124
ROT_CELL, ROT_VALUE, ROTED = 154, 20173, 26407
PAYLOAD = b"psi seam payload \x00\x7f"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


class K2SeamTests(unittest.TestCase):
    evidence = None

    @classmethod
    def setUpClass(cls):
        cc = shutil.which("cc")
        if cc is None:
            raise RuntimeError("oracle verification requires cc")
        tmp = tempfile.TemporaryDirectory(prefix="bolgeforge-seam-")
        cls.addClassCleanup(tmp.cleanup)
        cls.temporary = Path(tmp.name)
        cls.source_bytes = BASELINE.read_bytes()
        cls.T = [b for b in cls.source_bytes if 33 <= b <= 126]
        if len(cls.T) != CLEAN_CELLS:
            raise RuntimeError(f"unexpected clean cell count {len(cls.T)}")
        cls.binaries = {}
        for name, c_source in (("mb_ref", ROOT / "oracle/mb_ref.c"),
                               ("trace_loop", TOOLS / "trace_loop.c")):
            binary = cls.temporary / name
            subprocess.run([cc, "-O2", str(c_source), "-o", str(binary)],
                           check=True, capture_output=True)
            cls.binaries[name] = binary
        for name, cell, value, mirror in (
                ("candidate_psi_route_m281.mal", PLANT_LC, ZQ, True),
                ("candidate_unmirrored_edit.mal", PLANT_LC, ZQ, False)):
            (cls.temporary / name).write_bytes(cls.edit(cls.T, cell, value, mirror))
        # the temporary directory is cleaned before the report is written, so keep
        # everything the evidence record needs out of it
        cls.edited_bytes = (cls.temporary / "candidate_psi_route_m281.mal").read_bytes()
        cls.binary_sha256 = {f"<tmp>/{name}": sha256_bytes(binary.read_bytes())
                             for name, binary in cls.binaries.items()}

    @staticmethod
    def edit(T, cell, value, mirror=True):
        out = list(T)
        out[cell] = value
        if mirror:
            out[cell + MIRROR] = value
        return selector_dev.rebuild(out)

    @staticmethod
    def shown(path):
        try:
            return str(Path(path).relative_to(ROOT))
        except ValueError:
            return f"<tmp>/{Path(path).name}"

    def oracle(self, program, feed):
        argv = [str(self.binaries["mb_ref"]), str(program), "200000000"]
        proc = subprocess.run(argv, input=feed, capture_output=True, timeout=180, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode(errors="replace"))
        return proc

    def tracer(self, program, extra):
        argv = [str(self.binaries["trace_loop"]), str(program), "70000000"] + extra
        proc = subprocess.run(argv, input=b"C" + PAYLOAD, capture_output=True,
                              timeout=180, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode(errors="replace"))
        return proc.stdout.decode(errors="replace")

    def test_shared_prefix_ends_on_one_branch_instruction(self):
        mem = selector_dev.pad(self.T)
        q = selector_dev.sim(mem, b"Q", max_steps=BEFORE_BRANCH_CELL)
        c = selector_dev.sim(mem, b"C" + PAYLOAD, max_steps=BEFORE_BRANCH_CELL)
        self.assertEqual((q["c"], c["c"]), (BRANCH_CELL - 1, BRANCH_CELL - 1))
        self.assertEqual((q["d"], c["d"]), (ROT_CELL, 35))
        q = selector_dev.sim(mem, b"Q", max_steps=AT_BRANCH_CELL)
        c = selector_dev.sim(mem, b"C" + PAYLOAD, max_steps=AT_BRANCH_CELL)
        self.assertEqual((q["c"], c["c"]), (BRANCH_CELL, BRANCH_CELL))
        self.assertEqual((q["d"], c["d"]), (26408, 34))
        type(self).branch_states = {"at_step": AT_BRANCH_CELL, "cell": BRANCH_CELL,
                                    "Q": {"c": q["c"], "d": q["d"], "a": q["a"]},
                                    "C": {"c": c["c"], "d": c["d"], "a": c["a"]}}

    def test_divergence_is_pure_d_routing(self):
        mem = selector_dev.pad(self.T)
        q = selector_dev.sim(mem, b"Q", max_steps=AFTER_BRANCH)
        c = selector_dev.sim(mem, b"C" + PAYLOAD, max_steps=AFTER_BRANCH)
        # the cell the branch `i` reads holds the same value in both runs,
        # so nothing about the *value* differs: only where d points
        self.assertEqual(q["mem"][26408], c["mem"][26408])
        self.assertEqual(q["mem"][26408], LOOP_ENTRY - 1)
        self.assertEqual(c["mem"][34], 35)
        self.assertEqual(q["c"], LOOP_ENTRY)          # 25975 is the target; c++ -> 25976
        self.assertEqual(c["c"], 36)                  # 35 is the target;   c++ -> 36 (`v`)
        self.assertEqual(selector_dev.rot_op(ROT_VALUE), ROTED)
        self.assertEqual(c["mem"][ROT_CELL], ROT_VALUE)   # C rotated a different cell
        self.assertEqual(q["mem"][ROT_CELL], ROTED)       # Q's `*` at d=154 minted 26407
        type(self).d_routing = {
            "shared_i_cell": BRANCH_CELL, "shared_i_step": AT_BRANCH_CELL,
            "mem_26408_both": q["mem"][26408], "mem_34_C": c["mem"][34],
            "c_after_branch": c["c"], "q_after_branch": q["c"],
            "mem154_C": c["mem"][ROT_CELL], "mem154_Q": q["mem"][ROT_CELL],
            "rot_20173": selector_dev.rot_op(ROT_VALUE),
        }

    def test_plants_are_mirrored_at_26414(self):
        for cell in (34, 36, 38, PLANT_LC, PLANT_LQ):
            self.assertEqual(self.T[cell], self.T[cell + MIRROR],
                             f"plant {cell} is not mirrored at {cell + MIRROR}")
        self.assertEqual((self.T[PLANT_LC], self.T[PLANT_LQ], self.T[38]), (ZC, ZQ, Y))
        self.assertEqual(self.T[34], 35)          # Z-1 with Z=36
        self.assertEqual(self.T[36], 45)          # char_for_op(36, "v")

    def test_S_identity_arithmetic(self):
        self.assertEqual(ZC + 154 - ZQ, 187)          # published S (rotates cell 187)
        self.assertEqual(ZQ + 154 - ZQ, ROT_CELL)     # zC = zQ -> S = 154
        self.assertEqual(selector_dev.crazy_op(81, Y), 29446)       # vQ
        self.assertEqual(selector_dev.crazy_op(67, Y), 29544)       # vC

    def test_unmirrored_single_edit_breaks_the_quine_at_that_byte(self):
        program = self.temporary / "candidate_unmirrored_edit.mal"
        proc = self.oracle(program, b"Q")
        source = program.read_bytes()
        self.assertEqual(len(proc.stdout), len(source))
        diff = [i for i, (x, y) in enumerate(zip(proc.stdout, source)) if x != y]
        self.assertEqual(diff, [40])
        self.assertEqual((proc.stdout[40], source[40]), (ZC, ZQ))
        type(self).unmirrored_diff = {"positions": diff, "printed": proc.stdout[40],
                                      "source": source[40],
                                      "reading": ("the QUINE branch prints the plant's mirror at "
                                                 "cell+26414, so an edit that is not mirrored "
                                                 "desynchronises the quine at exactly that byte")}

    def test_mirrored_edit_holds_the_quine_invariant(self):
        program = self.temporary / "candidate_psi_route_m281.mal"
        proc = self.oracle(program, b"Q")
        source = program.read_bytes()
        self.assertEqual(proc.stdout, source)
        self.assertEqual(len(source), len(self.source_bytes))
        self.assertNotEqual(sha256_bytes(source), sha256_bytes(self.source_bytes))

    def test_mirrored_edit_reroutes_c_into_the_print_loop(self):
        baseline = self.oracle(BASELINE, b"C" + PAYLOAD)
        self.assertEqual(baseline.stdout, b"")
        program = self.temporary / "candidate_psi_route_m281.mal"
        edited = self.oracle(program, b"C" + PAYLOAD)
        source = program.read_bytes()
        self.assertEqual(edited.stdout, source)        # C now prints its own image
        self.assertNotEqual(edited.stdout, PAYLOAD)
        summary = [line for line in self.tracer(program, ["-f", "25976", "-w", "0"]).splitlines()
                   if line.startswith(("steps=", "trigger:", "stdin reads"))]
        self.assertIn("steps=62239932 halt=v prints=53562 out_bytes=53562 anomalies=0", summary)
        self.assertIn("trigger: step=25532 c=25976 d=26409 a=26407 (prints=53562)", summary)
        type(self).reroute = {
            "baseline_C_stdout_bytes": len(baseline.stdout),
            "edited_C_stdout_bytes": len(edited.stdout),
            "edited_C_equals_source": edited.stdout == source,
            "edited_C_equals_payload": edited.stdout == PAYLOAD,
            "edited_candidate_sha256": sha256_bytes(source),
            "tracer_summary": summary,
        }

    def test_c_branch_still_does_not_echo_payload(self):
        edited = self.oracle(self.temporary / "candidate_psi_route_m281.mal", b"C" + PAYLOAD)
        self.assertNotIn(PAYLOAD, edited.stdout)
        self.assertNotEqual(edited.stdout, b"")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, help="new, non-existing evidence directory")
    args = parser.parse_args()
    if args.evidence is not None:
        args.evidence.mkdir(parents=False, exist_ok=False)
    K2SeamTests.evidence = args.evidence
    started = time.monotonic()
    captured = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(K2SeamTests)
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
            "inputs_sha256": {
                K2SeamTests.shown(BASELINE): sha256_bytes(BASELINE.read_bytes()),
                K2SeamTests.shown(ROOT / "oracle/mb_ref.c"):
                    sha256_bytes((ROOT / "oracle/mb_ref.c").read_bytes()),
                K2SeamTests.shown(TOOLS / "trace_loop.c"):
                    sha256_bytes((TOOLS / "trace_loop.c").read_bytes()),
                K2SeamTests.shown(TOOLS / "selector_dev.py"):
                    sha256_bytes((TOOLS / "selector_dev.py").read_bytes()),
                K2SeamTests.shown(Path(__file__).resolve()): sha256_bytes(
                    Path(__file__).read_bytes()),
            },
            "oracle_binaries_sha256": K2SeamTests.binary_sha256,
            "branch_states_at_shared_i": getattr(K2SeamTests, "branch_states", None),
            "d_routing": getattr(K2SeamTests, "d_routing", None),
            "unmirrored_edit_diff": getattr(K2SeamTests, "unmirrored_diff", None),
            "reroute": getattr(K2SeamTests, "reroute", None),
            "edit_spec": {"cell": PLANT_LC, "from": ZC, "to": ZQ,
                          "mirrored_at": PLANT_LC + MIRROR,
                          "consequence": "S = zC + 154 - zQ becomes 154, the cell Q's `*` "
                                         "rotates into the address 26407"},
            "claims": {
                "Q byte-exact after the mirrored edit": "DEMONSTRATED",
                "C branch re-routed from halt into the print loop by one mirrored byte edit":
                    "DEMONSTRATED",
                "Q/C divergence is pure d routing (cell read by the branch `i` holds the same "
                    "value in both branches)": "DEMONSTRATED",
                "the plant mirror at cell+26414 is load-bearing for the quine": "DEMONSTRATED",
                "C echoes the payload (CAT row)": "NOT_DEMONSTRATED — C prints its own image",
                "single program satisfying both QUINE and CAT rows (K2)": "NOT_DEMONSTRATED",
            },
            "not_demonstrated": ["payload echo in the C branch", "executable K2",
                                 "stable self-encrypting read/store loop", "two-engine parity"],
        }
        (args.evidence / "results.json").write_text(json.dumps(data, indent=2) + "\n",
                                                   encoding="utf-8")
        with (args.evidence / "candidate_psi_route_m281.mal").open("xb") as handle:
            handle.write(K2SeamTests.edited_bytes)
        hashes = {path.name: sha256_bytes(path.read_bytes())
                  for path in args.evidence.iterdir() if path.is_file()}
        (args.evidence / "hashes.json").write_text(json.dumps(hashes, indent=2) + "\n",
                                                  encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
