#!/usr/bin/env python3
"""K2 rail-read probe: can one mirrored image edit make the print loop READ?

The seam stage moved the C branch into the print loop; the store-depth stage
sized the loop body (2-3 `/`+`p` cycles per byte). This suite asks the next
mechanical question: is a read instruction reachable at all inside the running
print loop, and does a single mirrored edit survive it?

Method: trace the loop phase, take every cell the instruction pointer actually
visits, flip each one (mirrored at cell+26414) to the value whose rotating
decode is `/`, and measure. Recorded paths are repo-relative; temporary builds
appear as <tmp>/<basename>.

Run from any directory: python3 -B <this-file> [--evidence NEW_DIRECTORY].
Requires a C compiler. Evidence directories are created exclusively.
"""
import argparse
import contextlib
import hashlib
import io
import json
import platform
import re
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
sys.path[:0] = [str(TOOLS), str(ROOT)]

import selector_dev

MIRROR = 26414
IMAGE_CELLS = 52828
N = 59049
READ_IDX = selector_dev.XLAT1.index("/")
CANDIDATE = (EXPERIMENT / "evidence" / "K2_C_BRANCH_SEAM_20261018_I"
             / "candidate_psi_route_m281.mal")
TRACER_SOURCE = TOOLS / "trace_loop.c"
SELECTOR = TOOLS / "selector_dev.py"
PAYLOAD = b"Q" + bytes(range(40, 120))          # discriminator byte, then payload
SCREEN_CAP = "425532"
FULL_CAP = "70000000"
LOOP_TRIGGER = 25976
SEAM_STEP = 25532
WINDOW = 400000
QUINE_BYTES = 53562


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def read_value(cell):
    """Printable value whose decode at `cell` is the read instruction `/`."""
    return 33 + ((READ_IDX - cell) % 94)


def image_letter(T, cell):
    return selector_dev.XLAT1[(T[cell] - 33 + cell) % 94]


class K2RailReadTests(unittest.TestCase):
    evidence = None

    @classmethod
    def setUpClass(cls):
        cc = shutil.which("cc")
        if cc is None:
            raise RuntimeError("tracing requires cc")
        tmp = tempfile.TemporaryDirectory(prefix="bolgeforge-rail-")
        cls.addClassCleanup(tmp.cleanup)
        cls.temporary = Path(tmp.name)
        cls.tracer = cls.temporary / "trace_loop"
        subprocess.run([cc, "-O2", str(TRACER_SOURCE), "-o", str(cls.tracer)],
                       check=True, capture_output=True)
        # Captured here: addClassCleanup removes the temporary tree before the
        # report block runs, so anything read from it later is gone (stage K).
        cls.tracer_sha256 = sha256_bytes(cls.tracer.read_bytes())
        cls.T = [b for b in CANDIDATE.read_bytes() if 33 <= b <= 126]
        if len(cls.T) != IMAGE_CELLS:
            raise RuntimeError(f"unexpected clean cell count {len(cls.T)}")
        cls.source_head = CANDIDATE.read_bytes()[:12]
        cls.out = cls.temporary / "out.bin"
        cls.screen_baseline, _ = cls.run_tracer(CANDIDATE, SCREEN_CAP)
        cls.full_baseline, _ = cls.run_tracer(CANDIDATE, FULL_CAP)
        # Everything below is measured in setUpClass, not in the tests: unittest sorts
        # method names alphabetically, so a test that depends on another test's result is
        # a hidden ordering bug (stage L: `flips` ran before `loop_visits`).
        cls._trace_window()
        cls._screen_scan()
        cls._full_scan()

    @classmethod
    def _trace_window(cls):
        _, trace_text = cls.run_tracer(CANDIDATE, SCREEN_CAP, window=True)
        cls.visited, cls.first_fetch = {}, {}
        for line in trace_text.splitlines():
            m = re.match(r"^(\d+)\tc=(\d+)\td=(\d+)\t(\S)\t", line)
            if m:
                cell = int(m.group(2))
                cls.visited[cell] = cls.visited.get(cell, 0) + 1
                cls.first_fetch.setdefault(cell, (int(m.group(1)), m.group(4)))
        cls.editable = sorted(c for c in cls.visited if c + MIRROR < IMAGE_CELLS and c < N)

    @classmethod
    def _screen_scan(cls):
        cls.flips, cls.readers, cls.inert, cls.preamble_only = [], [], [], []
        for cell in cls.editable:
            fields, _ = cls.run_tracer(cls.flip(cell, read_value(cell)), SCREEN_CAP)
            row = {
                "cell": cell, "value": read_value(cell),
                "visits_in_window": cls.visited[cell],
                "steps": int(fields["steps"]), "prints": int(fields["prints"]),
                "preamble_reads": int(fields["preamble"]),
                "loop_reads": int(fields["loop"]),
                "out_bytes": int(fields["out_bytes"]), "halt": fields["halt"],
                "identical_prefix": (int(fields["steps"]) == int(cls.screen_baseline["steps"])
                                     and int(fields["prints"]) == int(cls.screen_baseline["prints"])
                                     and int(fields["out_bytes"]) == int(cls.screen_baseline["out_bytes"])),
            }
            cls.flips.append(row)
            if row["loop_reads"] > 0:
                cls.readers.append(row)
            elif row["preamble_reads"] > int(cls.screen_baseline["preamble"]):
                cls.preamble_only.append(row)
            if row["identical_prefix"]:
                cls.inert.append(row)
        cls.inert_detail = [
            {"cell": row["cell"], "first_fetch_step": cls.first_fetch[row["cell"]][0],
             "image_letter": image_letter(cls.T, row["cell"]),
             "executed_letter": cls.first_fetch[row["cell"]][1],
             "rewritten_before_fetch": (image_letter(cls.T, row["cell"])
                                        != cls.first_fetch[row["cell"]][1])}
            for row in cls.inert]

    @classmethod
    def _echo_run(cls, out, minimum=8):
        """Largest contiguous run of the stdin payload found in `out` (0 if under `minimum`)."""
        for k in range(len(PAYLOAD), minimum - 1, -1):
            if any(PAYLOAD[i:i + k] in out for i in range(len(PAYLOAD) - k + 1)):
                return k
        return 0

    @classmethod
    def _full_scan(cls):
        cls.full_flips = []
        for row in cls.readers:
            fields, _ = cls.run_tracer(cls.flip(row["cell"], row["value"]), FULL_CAP)
            out = cls.out.read_bytes()
            cls.full_flips.append({
                "cell": row["cell"], "screen_loop_reads": row["loop_reads"],
                "steps": int(fields["steps"]), "prints": int(fields["prints"]),
                "preamble_reads": int(fields["preamble"]),
                "loop_reads": int(fields["loop"]),
                "byte_exact": fields["byte_exact"], "halt": fields["halt"],
                "echo_run_of_stdin": cls._echo_run(out),
                "printed_head": list(out[:12]),
                "head_equals_image": list(out[:12]) == list(cls.source_head)})

    @classmethod
    def run_tracer(cls, program, cap, window=False):
        # -f is passed on EVERY run: without it the tracer never sets loop_active, so the
        # preamble/loop split collapses into the preamble counter (stage L artifact).
        argv = [str(cls.tracer), str(program), cap, "-f", str(LOOP_TRIGGER),
                "-o", str(cls.out)]
        tracefile = None
        if window:
            tracefile = cls.temporary / "window.trace"
            argv += ["-w", str(WINDOW), "-t", str(tracefile)]
        proc = subprocess.run(argv, input=PAYLOAD, capture_output=True, timeout=1800,
                              cwd=ROOT)
        assert proc.returncode == 0, proc.stderr.decode(errors="replace")
        text = proc.stdout.decode(errors="replace")
        fields = {}
        for line in text.splitlines():
            if line.startswith(("steps=", "stdin reads:")):
                fields.update(dict(re.findall(r"(\w+)=(\d+)", line)))
        fields["out_bytes"] = cls.out.stat().st_size
        sanity = re.search(r"SANITY out==src: (\d)", text)
        fields["byte_exact"] = bool(sanity and sanity.group(1) == "1")
        halt = re.search(r"halt=(\w+)", text)
        fields["halt"] = halt.group(1) if halt else "?"
        trig = re.search(r"trigger: step=(\d+) c=(\d+)", text)
        fields["trigger_step"] = int(trig.group(1)) if trig else None
        fields["trigger_cell"] = int(trig.group(2)) if trig else None
        return fields, (tracefile.read_text() if tracefile else "")

    @classmethod
    def flip(cls, cell, value):
        """Mirror a single image cell and write the program into <tmp>."""
        out = list(cls.T)
        out[cell] = value
        out[cell + MIRROR] = value
        program = cls.temporary / "flipped.mal"
        program.write_bytes(selector_dev.rebuild(out))
        return program

    def test_baseline_is_the_quine_and_never_reads_in_loop(self):
        base = type(self).full_baseline
        self.assertEqual(int(base["prints"]), QUINE_BYTES)
        self.assertTrue(base["byte_exact"])
        self.assertEqual(int(base["loop"]), 0)
        self.assertEqual(int(base["preamble"]), 1)
        self.assertEqual(int(base["anomalies"]), 0)
        # The phase split is auditable: the loop begins one step after the shared `i`.
        self.assertEqual(base["trigger_step"], SEAM_STEP)
        self.assertEqual(base["trigger_cell"], LOOP_TRIGGER)

    def test_loop_visits_a_bounded_set_of_rail_cells(self):
        self.assertTrue(type(self).visited)
        self.assertIn(0, type(self).visited)
        self.assertGreater(max(type(self).visited), 26400)
        self.assertEqual(len(type(self).editable),
                         len(type(self).visited) - sum(1 for c in type(self).visited
                                                       if c + MIRROR >= IMAGE_CELLS))
        self.assertEqual(len(type(self).flips), len(type(self).editable))

    def test_one_mirrored_rail_edit_makes_the_loop_phase_read_stdin(self):
        """The claim this stage exists to establish: reads INSIDE the print loop, not in
        the loader before it. `loop_reads` is the tracer's phase-B counter, so the trigger
        cell has to have been passed first."""
        readers = type(self).readers
        self.assertGreater(len(readers), 0)
        self.assertLess(len(readers), len(type(self).flips))
        self.assertTrue(all(r["loop_reads"] > 0 for r in readers), readers)
        # A loop read is only meaningful if the loader still read exactly what it reads
        # in the baseline: cell 26395 additionally perturbs the loader, so this is a
        # count, not an invariant.
        self.assertEqual(sum(1 for r in readers if r["preamble_reads"] == 1), len(readers) - 1)

    def test_flips_that_read_only_before_loop_entry_are_counted_separately(self):
        """A rail cell can also gain a read in the loader phase; that is not a loop read
        and it is recorded apart, so the headline count cannot silently absorb it."""
        rows = type(self).preamble_only
        self.assertTrue(rows)
        self.assertTrue(all(r["loop_reads"] == 0 for r in rows), rows)
        self.assertTrue(all(r["preamble_reads"] > int(type(self).screen_baseline["preamble"])
                            for r in rows), rows)
        self.assertEqual(len(type(self).readers) + len(rows) + len(
            [r for r in type(self).flips if r["loop_reads"] == 0
             and r["preamble_reads"] == int(type(self).screen_baseline["preamble"])]),
            len(type(self).flips))

    def test_no_single_flip_survives_to_a_byte_exact_quine(self):
        full = type(self).full_flips
        self.assertEqual(len(full), len(type(self).readers))
        self.assertEqual([f for f in full if f["byte_exact"]], [])

    def test_the_inert_flips_are_erased_by_self_modification_before_the_fetch(self):
        """The image value of these rail cells is not the value the machine fetches: the
        loader rewrites the instruction cell before it is ever executed, so an image edit
        there cannot route anything. This is the self-modification warning from the
        handoff, measured rather than assumed."""
        rows = type(self).inert_detail
        self.assertTrue(rows)
        self.assertTrue(all(r["rewritten_before_fetch"] for r in rows), rows)
        self.assertEqual(len(rows), len(type(self).inert))

    def test_reading_in_the_loop_does_not_print_what_was_read(self):
        """The C branch needs an echo, not a read: no loop-reading flip prints a run of
        eight or more consecutive stdin bytes, and the ones that keep printing print the
        image they were given."""
        broken = type(self).full_flips
        self.assertTrue(broken)
        self.assertEqual([f for f in broken if f["echo_run_of_stdin"] >= 8], [], broken)
        self.assertTrue(all(f["prints"] < QUINE_BYTES or not f["byte_exact"] for f in broken))
        self.assertTrue(all(f["halt"] == "v" for f in broken), broken)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    if args.evidence is not None and args.evidence.exists():
        parser.error(f"evidence directory already exists: {args.evidence}")
    if args.evidence is not None:
        args.evidence.mkdir(parents=True)
    started = time.monotonic()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(K2RailReadTests)
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
            "inputs_sha256": {
                str(CANDIDATE.relative_to(ROOT)): sha256_bytes(CANDIDATE.read_bytes()),
                str(TRACER_SOURCE.relative_to(ROOT)): sha256_bytes(TRACER_SOURCE.read_bytes()),
                str(SELECTOR.relative_to(ROOT)): sha256_bytes(SELECTOR.read_bytes()),
                str(Path(__file__).resolve().relative_to(ROOT)):
                    sha256_bytes(Path(__file__).read_bytes()),
            },
            "oracle_binaries_sha256": {f"<tmp>/{K2RailReadTests.tracer.name}":
                                       K2RailReadTests.tracer_sha256},
            "method": {
                "edit": "one image cell, mirrored at cell+26414",
                "edit_value": "33 + ((xlat1_index('/') - cell) % 94)",
                "screen_cap_steps": int(SCREEN_CAP), "full_run_cap_steps": int(FULL_CAP),
                "trace_window_steps": WINDOW,
                "phase_trigger": f"-f {LOOP_TRIGGER} on every run; phase A = loader, "
                                 f"phase B = print loop",
                "stdin": "byte 81 (`Q`, the branch discriminator) then bytes 40..119",
                "echo_test": ("longest contiguous run of the stdin payload found in the "
                              "printed stream, minimum reported length 8"),
            },
            "baseline_full_run": K2RailReadTests.full_baseline,
            "baseline_screen_run": K2RailReadTests.screen_baseline,
            "rail_cells_visited_in_window": len(K2RailReadTests.visited),
            "mirror_editable_cells": len(K2RailReadTests.editable),
            "highest_visited_cell": max(K2RailReadTests.visited),
            "visited_cells": sorted(K2RailReadTests.visited),
            "flips": K2RailReadTests.flips,
            "loop_read_cells": [r["cell"] for r in K2RailReadTests.readers],
            "loop_read_gainers": len(K2RailReadTests.readers),
            "max_loop_reads_screen": max(r["loop_reads"] for r in K2RailReadTests.readers),
            "loader_read_only_cells": [r["cell"] for r in K2RailReadTests.preamble_only],
            "loop_read_gainers_full_run": K2RailReadTests.full_flips,
            "max_loop_reads_full": max(f["loop_reads"] for f in K2RailReadTests.full_flips),
            "inert_flips": K2RailReadTests.inert_detail,
            "claims": {
                f"the print LOOP executes `/` on stdin after one mirrored rail edit "
                f"({len(K2RailReadTests.readers)} "
                f"of {len(K2RailReadTests.editable)} rail cells, up to "
                f"{max(f['loop_reads'] for f in K2RailReadTests.full_flips)} loop reads in "
                f"a full run)": "DEMONSTRATED",
                "no single mirrored rail edit yields a byte-exact quine that also reads":
                    "DEMONSTRATED",
                "no single mirrored rail edit echoes eight or more consecutive stdin bytes":
                    "DEMONSTRATED",
                "rail cells rewritten before their first fetch cannot be routed by an "
                "image edit (self-modification)": "DEMONSTRATED",
                "every loop-reading flip ends on a planted `v`": "DEMONSTRATED",
                "a two-edit read-then-restore cycle that keeps the quine":
                    "NOT_DEMONSTRATED",
                "storing a read byte into a cell the loader later prints":
                    "NOT_DEMONSTRATED",
                "an executable C-branch read/store loop": "NOT_DEMONSTRATED",
                "C echoes stdin bytes (CAT row)": "NOT_DEMONSTRATED",
                "single program satisfying both QUINE and CAT rows (K2)":
                    "NOT_DEMONSTRATED",
            },
            "not_demonstrated": [
                "multi-cell (read + accumulator restore) edit sets",
                "payload echo in the C branch", "executable K2",
                "two-engine parity for the flipped programs (only the compiled tracer was run)",
                "that the 6,221 cells outside the quine image can host a cat loop"],
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
