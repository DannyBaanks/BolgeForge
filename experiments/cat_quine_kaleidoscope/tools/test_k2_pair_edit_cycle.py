#!/usr/bin/env python3
"""K2 pair-edit probe: can a TWO-cell mirrored edit set read a byte and store it?

Stage M established that one mirrored rail edit can put a `/` inside the running print
loop, and that the read never becomes an echo: `/` writes the accumulator `a`, and `a`
is exactly what the loop's `<` prints, so a read in the print loop is structurally
destructive. The handoff's next question was whether a SECOND edited cell can repair
that - read on the rail, restore before the next `<`.

This suite measures the two-cell version instead of assuming it. Method: take every pair
of cells the instruction pointer visits in consecutive steps of the loop phase, edit the
first to `/` and the second to each instruction letter, and ask the trace whether a store
follows the read. Then two questions, kept apart on purpose:

  * dynamics - does a read->store cycle actually execute, and does the stored value
    depend on the stdin byte? Dependency is tested twice: against the crazy table, and by
    feeding a different byte and watching the stored value move. Every event is attributed
    to the cell the machine EXECUTED, not the cell that was edited - a two-cell edit moves
    the trajectory, so some cycles run at cells the edit never touched, and the tracer
    skips steps whose cell holds no printable instruction (gaps are measured in steps).
  * information - can the byte be recovered from the stored value(s) at all, measured as
    an injectivity census over all 59,049 cell states.

Recorded paths are repo-relative; temporary builds appear as <tmp>/<basename>.

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
from collections import Counter
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
P9 = (1, 9, 81, 729, 6561)
CANDIDATE = (EXPERIMENT / "evidence" / "K2_C_BRANCH_SEAM_20261018_I"
             / "candidate_psi_route_m281.mal")
TRACER_SOURCE = TOOLS / "trace_loop.c"
SELECTOR = TOOLS / "selector_dev.py"
PAYLOAD = b"Q" + bytes(range(40, 120))          # discriminator byte, then payload
PROBE_BYTE = 187                                # replacement byte for the perturbation run
SCREEN_CAP = "425532"
FULL_CAP = "70000000"
LOOP_TRIGGER = 25976                            # cell at which the loop phase begins
SEAM_STEP = 25532                               # step at which it is entered
GEOMETRY_WINDOW = 400000                        # loop steps traced to find adjacent pairs
RUN_WINDOW = 24500                              # loop steps traced per pair run
MAX_STORE_GAP = 8                               # steps allowed between a read and its store
SUCCESSORS = list("p*<ji/o")
QUINE_BYTES = 53562
STORAGE_DOMAIN = tuple(range(256)) + (59048,)   # `/` yields a raw byte, or 3^10-1 at EOF


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def edit_value(letter, cell):
    """Printable value whose rotating decode at `cell` is `letter`."""
    return 33 + ((selector_dev.XLAT1.index(letter) - cell) % 94)


def trits(value):
    return tuple(value // p % 9 for p in P9)


def store_map(old):
    """Byte -> stored value for one `p` into a cell holding `old`.

    A byte has zero base-9 digits above position 2, so for b < 256 the output is a
    3-digit map translated by a constant depending only on `old`'s top two digits. That
    is what makes the full 59,049-state census cheap; the suite checks it against a
    direct crazy_op evaluation before trusting any of its numbers.
    """
    d = trits(old)
    key = d[:3]
    cached = store_map.CACHE.get(key)
    if cached is None:
        cached = []
        for b in STORAGE_DOMAIN[:-1]:
            bd = trits(b)
            cached.append(sum(selector_dev.CT9[key[j]][bd[j]] * P9[j] for j in range(3)))
        store_map.CACHE[key] = cached
    offset = selector_dev.CT9[d[3]][0] * 729 + selector_dev.CT9[d[4]][0] * 6561
    return [v + offset for v in cached] + [selector_dev.crazy_op(59048, old)]


store_map.CACHE = {}


def store_map_control(old):
    """The same map, evaluated directly - the control for store_map()."""
    return [selector_dev.crazy_op(b, old) for b in STORAGE_DOMAIN]


def injectivity_census():
    """Per-cell-state ambiguity of ONE store, over every state a cell can hold."""
    injective, ambiguity, histogram = [], 0, Counter()
    for old in range(N):
        distinct = Counter(store_map(old))
        lost = len(STORAGE_DOMAIN) - len(distinct)
        histogram[lost] += 1
        ambiguity = max(ambiguity, max(distinct.values()))
        if lost == 0:
            injective.append(old)
    return injective, ambiguity, histogram


# ------------------------------------------------------------------ the algebra questions
def joint_injectivity(old1, old2):
    """Distinct outcomes of one byte read and stored into TWO different cells."""
    return len({(selector_dev.crazy_op(b, old1), selector_dev.crazy_op(b, old2))
                for b in STORAGE_DOMAIN})


def repeat_in_same_cell(old):
    """Same byte stored twice into one cell: the second store sees the first result."""
    return Counter(selector_dev.crazy_op(b, selector_dev.crazy_op(b, old))
                   for b in STORAGE_DOMAIN)


def two_bytes_same_cell(old):
    """Two different bytes stored in sequence into one cell - only the last survives."""
    finals = Counter()
    for b1 in STORAGE_DOMAIN:
        middle = selector_dev.crazy_op(b1, old)
        for b2 in STORAGE_DOMAIN:
            finals[selector_dev.crazy_op(b2, middle)] += 1
    return finals


class K2PairEditTests(unittest.TestCase):
    evidence = None

    @classmethod
    def setUpClass(cls):
        cc = shutil.which("cc")
        if cc is None:
            raise RuntimeError("tracing requires cc")
        tmp = tempfile.TemporaryDirectory(prefix="bolgeforge-pair-")
        cls.addClassCleanup(tmp.cleanup)
        cls.temporary = Path(tmp.name)
        cls.tracer = cls.temporary / "trace_loop"
        subprocess.run([cc, "-O2", str(TRACER_SOURCE), "-o", str(cls.tracer)],
                       check=True, capture_output=True)
        # Captured here: addClassCleanup removes the temporary tree before the report
        # block runs (stage K).
        cls.tracer_sha256 = sha256_bytes(cls.tracer.read_bytes())
        cls.T = [b for b in CANDIDATE.read_bytes() if 33 <= b <= 126]
        if len(cls.T) != IMAGE_CELLS:
            raise RuntimeError(f"unexpected clean cell count {len(cls.T)}")
        cls.source_head = CANDIDATE.read_bytes()[:12]
        cls.out = cls.temporary / "out.bin"
        cls.screen_baseline, _ = cls.run_tracer(CANDIDATE, SCREEN_CAP)
        cls.full_baseline, _ = cls.run_tracer(CANDIDATE, FULL_CAP)
        # All measurement happens in setUpClass: unittest sorts method names
        # alphabetically, so a test that depends on another test's results is a hidden
        # ordering bug (stage L).
        cls._pairs()
        cls._pair_scan()
        cls._cycle_check()
        cls._full_pair_scan()
        cls._echo_check()
        cls._algebra()

    # ---------------------------------------------------------------------------- traces
    @classmethod
    def run_tracer(cls, program, cap, window=None, payload=PAYLOAD):
        # -f is passed on EVERY run: without it the tracer never sets loop_active, so the
        # preamble/loop split collapses into the preamble counter (stage L artifact).
        argv = [str(cls.tracer), str(program), cap, "-f", str(LOOP_TRIGGER),
                "-o", str(cls.out)]
        tracefile = None
        if window is not None:
            tracefile = cls.temporary / "trace.txt"
            argv += ["-w", str(window), "-t", str(tracefile)]
        proc = subprocess.run(argv, input=payload, capture_output=True, timeout=1800,
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
    def pair_program(cls, cell, successor_letter):
        """Two mirrored image edits: `/` at `cell`, `successor_letter` at `cell+1`.

        One file per edit set: a later phase re-runs these programs, and a shared
        filename would silently run the last build for every row.
        """
        out = list(cls.T)
        first = edit_value("/", cell)
        second = edit_value(successor_letter, cell + 1)
        for index, value in ((cell, first), (cell + MIRROR, first),
                             (cell + 1, second), (cell + 1 + MIRROR, second)):
            if index < IMAGE_CELLS:
                out[index] = value
        program = cls.temporary / f"pair_{cell}_{ord(successor_letter)}.mal"
        program.write_bytes(selector_dev.rebuild(out))
        return program

    @classmethod
    def _pairs(cls):
        """Cells the loop visits in CONSECUTIVE steps, i.e. executable as `/` then X."""
        _, trace_text = cls.run_tracer(CANDIDATE, SCREEN_CAP, window=GEOMETRY_WINDOW)
        seq = [int(m.group(1)) for m in
               (re.match(r"^\d+\tc=(\d+)", line) for line in trace_text.splitlines()) if m]
        cls.traced_steps = len(seq)
        cls.pairs = {}
        for left, right in zip(seq, seq[1:]):
            if right == left + 1 and left >= LOOP_TRIGGER and right + MIRROR < IMAGE_CELLS:
                cls.pairs[left] = cls.pairs.get(left, 0) + 1

    STORE_RE = re.compile(r"\t([p\*]) d=(\d+):(\d+)->(\d+)")
    READ_RE = re.compile(r"\tIN:(\d+)")
    LINE_RE = re.compile(r"^(\d+)\tc=(\d+)\td=(\d+)\t(\S)\ta=(\d+)")

    @classmethod
    def _pair_scan(cls):
        cls.rows = []
        for cell in sorted(cls.pairs, key=lambda k: -cls.pairs[k]):
            for letter in SUCCESSORS:
                program = cls.pair_program(cell, letter)
                fields, trace_text = cls.run_tracer(program, SCREEN_CAP, window=RUN_WINDOW)
                lines = trace_text.splitlines()
                heads = [cls.LINE_RE.match(line) for line in lines]
                steps = [int(h.group(1)) if h else -1 for h in heads]
                reads = [i for i, line in enumerate(lines) if cls.READ_RE.search(line)]
                near, immediate = [], None
                for ordinal, i in enumerate(reads):
                    for j in range(i + 1, len(lines)):
                        m = cls.STORE_RE.search(lines[j])
                        if not m:
                            continue
                        gap = steps[j] - steps[i]
                        if gap > MAX_STORE_GAP:
                            break
                        event = cls._event(lines, i, j, m, ordinal, fields, cell)
                        near.append(event)
                        if gap == 1 and immediate is None:
                            immediate = event
                        break
                row = {"cell": cell, "pair_visits": cls.pairs[cell], "successor": letter,
                       "loop_reads": int(fields["loop"]),
                       "preamble_reads": int(fields["preamble"]),
                       "steps": int(fields["steps"]), "prints": int(fields["prints"]),
                       "halt": fields["halt"], "traced_reads": len(reads),
                       f"stores_within_{MAX_STORE_GAP}_steps": len(near),
                       "immediate_store": immediate}
                row["program"] = program
                cls.rows.append(row)
        cls.reading_rows = [r for r in cls.rows if r["loop_reads"] > 0]
        cls.cycle_rows = [r for r in cls.rows if r["immediate_store"]]

    @classmethod
    def _event(cls, lines, read_index, store_index, store_match, ordinal, fields,
               edited_cell):
        """One read->store event, with the cells the machine ACTUALLY executed.

        Three things a naive reading gets wrong, and this suite records all three:
        the traced lines are not consecutive steps (a cell outside 33..126 executes
        nothing and is skipped by the tracer, so `gap` is measured in STEPS); the edited
        cell is not automatically the cell that runs (a two-cell edit reroutes the
        trajectory, and the loader's own self-modification can put a read/store pair in
        motion elsewhere on the rail); and the store's data cell is not the cell the
        store instruction sits in. Stage N collapsed all of these onto the edited cell.
        """
        read_head, store_head = cls.LINE_RE.match(lines[read_index]), \
            cls.LINE_RE.match(lines[store_index])
        read_exec, store_exec = int(read_head.group(2)), int(store_head.group(2))
        return {"step_gap": int(store_head.group(1)) - int(read_head.group(1)),
                "line_gap": store_index - read_index, "op": store_match.group(1),
                "store_cell": int(store_match.group(2)),
                "old": int(store_match.group(3)), "new": int(store_match.group(4)),
                "byte": int(cls.READ_RE.search(lines[read_index]).group(1)),
                "read_ordinal": ordinal,
                "payload_index": int(fields["preamble"]) + ordinal,
                "read_step": int(read_head.group(1)), "store_step": int(store_head.group(1)),
                "read_exec_cell": read_exec, "read_exec_letter": read_head.group(4),
                "store_exec_cell": store_exec, "store_exec_letter": store_head.group(4),
                "at_edited_cell": read_exec in (edited_cell, edited_cell + MIRROR),
                "store_at_edited_successor": store_exec in (edited_cell + 1,
                                                            edited_cell + 1 + MIRROR)}

    @classmethod
    def _first_cycle(cls, lines, read_exec_cell, store_exec_cell):
        """The first read->store one-step cycle at these two EXECUTED cells in a trace."""
        heads = [cls.LINE_RE.match(line) for line in lines]
        for i, line in enumerate(lines):
            read = cls.READ_RE.search(line)
            if not read or int(heads[i].group(2)) != read_exec_cell:
                continue
            for j in range(i + 1, len(lines)):
                store = cls.STORE_RE.search(lines[j])
                if not store:
                    continue
                if (int(heads[j].group(1)) - int(heads[i].group(1)) != 1
                        or int(heads[j].group(2)) != store_exec_cell):
                    break
                return {"read_step": int(heads[i].group(1)),
                        "store_step": int(heads[j].group(1)),
                        "byte": int(read.group(1)), "op": store.group(1),
                        "store_cell": int(store.group(2)), "old": int(store.group(3)),
                        "new": int(store.group(4))}
        return None

    @classmethod
    def _cycle_check(cls):
        """Byte dependence, checked twice: against the crazy table and against stdin."""
        cls.cycles, cls.controls, cls.perturbations = [], [], []
        for row in cls.cycle_rows:
            store = row["immediate_store"]
            byte, old, new = store["byte"], store["old"], store["new"]
            if store["op"] == "p":
                predicted = selector_dev.crazy_op(byte, old)
                depends = new == predicted
            else:
                predicted = selector_dev.rot_op(old)
                depends = False           # rot(old) has no byte operand at all
            record = dict(store, read_cell=row["cell"], successor=row["successor"],
                          byte=byte, predicted=predicted, depends_on_byte=depends)
            (cls.cycles if store["op"] == "p" else cls.controls).append(record)
            # Feed a different byte at the position this read consumed and watch the
            # stored value move. Reads that hit EOF (> len(payload)) have no byte to
            # perturb, and the branch discriminator is the first byte, never this one.
            index = store["payload_index"]
            base = {"read_cell": row["cell"], "successor": row["successor"],
                    "op": store["op"], "payload_index": index, "byte": byte,
                    "store_cell": store["store_cell"], "old": old, "new": new,
                    "read_exec_cell": store["read_exec_cell"],
                    "store_exec_cell": store["store_exec_cell"],
                    "at_edited_cell": store["at_edited_cell"],
                    "store_at_edited_successor": store["store_at_edited_successor"]}
            if index >= len(PAYLOAD):
                cls.perturbations.append(dict(base, status="EOF_read_no_byte_to_perturb"))
                continue
            probe = bytearray(PAYLOAD)
            probe[index] = PROBE_BYTE
            fields, trace_text = cls.run_tracer(row["program"], SCREEN_CAP,
                                               window=RUN_WINDOW, payload=bytes(probe))
            found = cls._first_cycle(trace_text.splitlines(), store["read_exec_cell"],
                                     store["store_exec_cell"])
            if found is None:
                cls.perturbations.append(dict(base, status="cycle_did_not_recur_under_probe",
                                              probe_steps=int(fields["steps"]),
                                              probe_halt=fields["halt"]))
                continue
            if found["op"] == "p":
                expectation = selector_dev.crazy_op(PROBE_BYTE, found["old"])
            else:
                expectation = selector_dev.rot_op(found["old"])
            # A different cell state at store time means the trajectory diverged before
            # this event: the run is no longer the same cycle, so it cannot decide
            # anything about byte dependence.
            status = ("reproduced" if found["old"] == old and found["op"] == store["op"]
                      and found["byte"] == PROBE_BYTE else "diverged_before_the_store")
            cls.perturbations.append(dict(
                base, status=status, probe=found, probe_read_cell=store["read_exec_cell"],
                expected_under_probe=expectation,
                value_changed=found["new"] != new,
                matches_probe_prediction=found["new"] == expectation))
        cls.confirmed = [p for p in cls.perturbations if p["status"] == "reproduced"
                         and p["op"] == "p" and p["value_changed"]
                         and p["matches_probe_prediction"]]
        cls.rot_control = [p for p in cls.perturbations if p["status"] == "reproduced"
                           and p["op"] == "*"]
        # the two mechanisms are different findings and stay separated
        cls.cycles_on_edit = [c for c in cls.cycles if c["at_edited_cell"]
                              and c["store_at_edited_successor"]]
        cls.cycles_collateral = [c for c in cls.cycles if not c["at_edited_cell"]]
        cls.confirmed_on_edit = [p for p in cls.confirmed if p["at_edited_cell"]
                                 and p["store_at_edited_successor"]]

    @classmethod
    def _echo_run(cls, out, minimum=8):
        """Largest contiguous run of the stdin payload found in `out` (0 if under `minimum`)."""
        for k in range(len(PAYLOAD), minimum - 1, -1):
            if any(PAYLOAD[i:i + k] in out for i in range(len(PAYLOAD) - k + 1)):
                return k
        return 0

    @classmethod
    def _full_pair_scan(cls):
        cls.full_rows = []
        for row in cls.reading_rows:
            fields, _ = cls.run_tracer(row["program"], FULL_CAP)
            out = cls.out.read_bytes()
            cls.full_rows.append({
                "cell": row["cell"], "successor": row["successor"],
                "screen_loop_reads": row["loop_reads"],
                "steps": int(fields["steps"]), "prints": int(fields["prints"]),
                "preamble_reads": int(fields["preamble"]), "loop_reads": int(fields["loop"]),
                "byte_exact": fields["byte_exact"], "halt": fields["halt"],
                "echo_run_of_stdin": cls._echo_run(out, minimum=1),
                "printed_head": list(out[:12]),
                "head_equals_image": list(out[:12]) == list(cls.source_head)})

    @classmethod
    def _echo_check(cls):
        """Output-side control: does a print ever carry the stdin byte ITSELF?

        A `<` in the cell right after the read prints the accumulator the read has just
        filled, so a one-byte echo is expected geometrically. Whether the printed byte is
        that byte or an arithmetic coincidence is decided causally: same program, one
        different stdin byte, the output has to move with it.
        """
        cls.echoes = []
        for row in cls.reading_rows:
            if row["successor"] != "<":
                continue
            fields, _ = cls.run_tracer(row["program"], FULL_CAP)
            out = cls.out.read_bytes()
            index = int(fields["preamble"])          # first byte the loop phase consumes
            record = {"cell": row["cell"], "prints": int(fields["prints"]),
                      "loop_reads": int(fields["loop"]), "printed_head": list(out[:4]),
                      "first_print": out[0] if out else None,
                      "stdin_byte_at_that_read": PAYLOAD[index] if index < len(PAYLOAD)
                      else None,
                      "echo_run_of_stdin": cls._echo_run(out, minimum=1)}
            if index >= len(PAYLOAD):
                cls.echoes.append(dict(record, status="EOF_read_no_byte_to_probe"))
                continue
            probe = bytearray(PAYLOAD)
            probe[index] = PROBE_BYTE
            pfields, _ = cls.run_tracer(row["program"], FULL_CAP, payload=bytes(probe))
            pout = cls.out.read_bytes()
            record.update({"probe_prints": int(pfields["prints"]),
                           "probe_first_print": pout[0] if pout else None,
                           "probe_echo_run_of_stdin": cls._echo_run(pout, minimum=1)})
            if not out:
                status = "no_output"
            elif record["first_print"] != record["stdin_byte_at_that_read"]:
                status = "print_is_not_the_stdin_byte"
            elif record["probe_first_print"] == PROBE_BYTE:
                status = "stdin_byte_echoed"
            else:
                status = "output_did_not_move_with_the_byte"
            record["status"] = status
            cls.echoes.append(record)

    @classmethod
    def _algebra(cls):
        cls.injective, cls.max_ambiguity, cls.histogram = injectivity_census()
        cls.measured_states = sorted({c["old"] for c in cls.cycles})
        cls.reservoir = [0, 29524, 59048]        # the three values rot() fixes
        checked = list(range(0, N, 211)) + cls.measured_states + cls.reservoir
        cls.mismatch = [old for old in checked if store_map(old) != store_map_control(old)]
        cls.ambiguity = [{"old": old, "distinct_after_one_store": len(set(store_map(old))),
                          "candidates_per_observation": max(Counter(store_map(old)).values())}
                         for old in cls.measured_states + cls.reservoir]
        cls.repeat = [{"old": old,
                       "single": max(Counter(store_map(old)).values()),
                       "stored_twice": max(repeat_in_same_cell(old).values()),
                       "distinct_after_twice": len(repeat_in_same_cell(old))}
                      for old in cls.measured_states + cls.reservoir]
        cls.two_bytes_one_cell = [
            {"old": old, "possible_byte_pairs": len(STORAGE_DOMAIN) ** 2,
             "distinct_finals": len(two_bytes_same_cell(old)),
             "max_pairs_per_final": max(two_bytes_same_cell(old).values())}
            for old in cls.measured_states[:1] + cls.reservoir]
        cls.joint = [{"first": a, "second": b, "distinct_outcomes": joint_injectivity(a, b)}
                     for a in cls.measured_states + cls.reservoir
                     for b in cls.measured_states + cls.reservoir]
        cls.injective_rail_pairs = [
            [row["first"], row["second"]] for row in cls.joint
            if row["distinct_outcomes"] == len(STORAGE_DOMAIN)
            and row["first"] < row["second"]
            and row["first"] in cls.measured_states
            and row["second"] in cls.measured_states]

    # --------------------------------------------------------------------------- tests
    def test_baseline_is_the_quine_and_pair_geometry_is_measured(self):
        base = type(self).full_baseline
        self.assertEqual(int(base["prints"]), QUINE_BYTES)
        self.assertTrue(base["byte_exact"])
        self.assertEqual(int(base["loop"]), 0)
        self.assertEqual(base["trigger_step"], SEAM_STEP)
        self.assertEqual(base["trigger_cell"], LOOP_TRIGGER)
        self.assertEqual(type(self).traced_steps, GEOMETRY_WINDOW)
        self.assertTrue(type(self).pairs)
        self.assertTrue(all(cell >= LOOP_TRIGGER for cell in type(self).pairs))
        self.assertTrue(all(cell + 1 + MIRROR < IMAGE_CELLS for cell in type(self).pairs))

    def test_a_two_cell_edit_set_can_read_and_store_in_the_same_cycle(self):
        """The headline dynamic claim: `/` on a rail with a store instruction in the very
        next cell executes a read and then writes memory, inside the print loop."""
        self.assertEqual(len(type(self).rows), len(type(self).pairs) * len(SUCCESSORS))
        on_edit = type(self).cycles_on_edit
        self.assertTrue(on_edit)
        for record in on_edit:
            self.assertEqual(record["op"], "p")
            self.assertEqual(record["step_gap"], 1, record)
            self.assertEqual(record["read_exec_cell"], record["read_cell"])
            self.assertEqual(record["store_exec_cell"], record["read_cell"] + 1)
            self.assertEqual(record["new"], record["predicted"])
            self.assertTrue(record["depends_on_byte"])
            # a real cycle needs two different cells: the read writes `a`, the store
            # writes mem[d] where d has already moved on
            self.assertNotEqual(record["store_cell"], record["read_cell"])
            self.assertNotEqual(record["store_cell"], record["read_cell"] + 1)

    def test_events_are_attributed_to_the_cells_the_machine_executed(self):
        """The trace, not the edit list, decides where an event happened: a two-cell edit
        moves the trajectory, so some cycles run at cells the edit never touches, and the
        tracer skips steps whose cell holds no printable instruction."""
        for record in type(self).cycles + type(self).controls:
            self.assertEqual(record["read_exec_letter"], "/")
            self.assertEqual(record["store_exec_letter"], record["op"])
            self.assertGreaterEqual(record["step_gap"], 1)
            self.assertGreaterEqual(record["read_step"], SEAM_STEP)
        partition = type(self).cycles_on_edit + type(self).cycles_collateral
        self.assertEqual(len(partition), len(type(self).cycles),
                         [c["read_cell"] for c in type(self).cycles])
        for record in type(self).cycles_collateral:
            self.assertNotIn(record["read_exec_cell"],
                             (record["read_cell"], record["read_cell"] + MIRROR))

    def test_the_stored_value_moves_with_the_stdin_byte(self):
        """Prediction alone could be a coincidence of the operand order (T24). Re-running
        the same pair program with a different byte at the position that read consumed
        must move the stored value, and land on crazy(new_byte, old)."""
        self.assertTrue(type(self).confirmed)
        for record in type(self).confirmed:
            self.assertEqual(record["op"], "p")
            self.assertEqual(record["probe"]["byte"], PROBE_BYTE, record)
            self.assertTrue(record["value_changed"], record)
            self.assertTrue(record["matches_probe_prediction"], record)
        # the other half of the control: a rot store does not move at all when the byte
        # changes, so "byte-dependent" is not simply "the trace changed"
        self.assertTrue(type(self).rot_control)
        self.assertEqual([p for p in type(self).rot_control if p["value_changed"]], [])
        self.assertTrue(all(p["matches_probe_prediction"] for p in type(self).rot_control))

    def test_the_byte_dependent_stores_are_the_p_successors_not_the_rot_successors(self):
        """A `*` successor also stores, but its value is a function of the old cell only -
        counting it as a byte store would be a false positive."""
        self.assertTrue(type(self).controls)
        self.assertEqual([c for c in type(self).controls if c["depends_on_byte"]], [])
        for record in type(self).controls:
            self.assertEqual(record["new"], record["predicted"])
            self.assertEqual(record["predicted"],
                             record["old"] // 3 + (record["old"] % 3) * 19683)
        self.assertTrue(all(c["depends_on_byte"] for c in type(self).cycles))

    def test_one_store_does_not_determine_the_byte(self):
        """Recovering the byte from the stored value is injectivity, not arithmetic luck."""
        self.assertEqual(type(self).mismatch, [])      # fast census == direct evaluation
        self.assertEqual(len(type(self).injective), 162)
        self.assertEqual(type(self).max_ambiguity, 39)
        self.assertLess(len(type(self).injective), N)
        self.assertTrue(type(self).measured_states)
        for row in type(self).ambiguity:
            if row["old"] in type(self).measured_states:
                self.assertGreater(row["candidates_per_observation"], 1, row)

    def test_the_injectivity_census_is_highly_skewed(self):
        """The census result is not 'usually fine': record how bad the common case is."""
        hist = type(self).histogram
        self.assertEqual(hist.get(0, 0), len(type(self).injective))
        self.assertGreater(max(hist), 100)
        self.assertEqual(sum(hist.values()), N)

    def test_a_second_store_into_the_same_cell_never_narrows_the_byte(self):
        """Repeat-after-read in one cell cannot recover what the first store lost."""
        for row in type(self).repeat:
            self.assertGreaterEqual(row["stored_twice"], row["single"], row)
        self.assertTrue(any(row["stored_twice"] > row["single"] for row in type(self).repeat))
        for row in type(self).two_bytes_one_cell:
            self.assertLess(row["distinct_finals"], row["possible_byte_pairs"])

    def test_two_distinct_store_cells_recover_the_byte_only_with_a_reservoir_state(self):
        """The constructive half, and its limit: two observations of ONE byte can be
        injective, but among the cell states this machine actually reached, NO pair of two
        ordinary rail states does. Every full-recovery pairing needs one of the three
        values rot() fixes - 29524 with anything, or 0 together with 59048. Stage N reported
        a rail-rail exception (82, 26400); with the events attributed to the executed cells
        instead of the edited ones, state 82 is not reached at all and the exception
        disappears."""
        joint = {(r["first"], r["second"]): r["distinct_outcomes"] for r in type(self).joint}
        full = len(STORAGE_DOMAIN)
        self.assertTrue(type(self).measured_states)
        for old in type(self).measured_states + type(self).reservoir:
            self.assertEqual(joint[(old, 29524)], full)     # the reservoir works everywhere
            self.assertEqual(joint[(29524, old)], full)
        self.assertEqual(joint[(0, 59048)], full)
        self.assertEqual(joint[(59048, 0)], full)
        rail = [value for (first, second), value in joint.items()
                if first in type(self).measured_states
                and second in type(self).measured_states]
        self.assertEqual(len(rail), len(type(self).measured_states) ** 2)
        self.assertEqual(type(self).injective_rail_pairs, [])   # no reservoir-free pairing
        self.assertLess(max(rail), full, sorted(joint.items()))

    def test_a_two_cell_edit_makes_the_branch_print_one_stdin_byte(self):
        """The output-side positive result: a `<` immediately after the edited read prints
        the byte the read put in `a`. Proven causally, not by arithmetic: replace that stdin
        byte and the printed byte becomes the replacement. It is still ONE byte - no edit
        set echoes a run."""
        echoed = [e for e in type(self).echoes if e["status"] == "stdin_byte_echoed"]
        self.assertTrue(echoed, type(self).echoes)
        for e in echoed:
            self.assertEqual(e["first_print"], e["stdin_byte_at_that_read"], e)
            self.assertEqual(e["probe_first_print"], PROBE_BYTE, e)
            self.assertEqual(e["echo_run_of_stdin"], 1, e)
            # PROBE_BYTE is outside the payload by construction, so a print that moved to
            # it is off the payload: the echo length is exactly the one byte, never a run.
            self.assertNotIn(PROBE_BYTE, PAYLOAD)
            self.assertEqual(e["probe_echo_run_of_stdin"], 0, e)
        self.assertEqual([e for e in type(self).echoes if e["echo_run_of_stdin"] >= 8], [])

    def test_no_two_cell_edit_set_keeps_the_byte_exact_quine_or_echoes(self):
        full = type(self).full_rows
        self.assertEqual(len(full), len(type(self).reading_rows))
        self.assertEqual([f for f in full if f["byte_exact"]], [])
        self.assertEqual([f for f in full if f["echo_run_of_stdin"] >= 8], [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    if args.evidence is not None and args.evidence.exists():
        parser.error(f"evidence directory already exists: {args.evidence}")
    if args.evidence is not None:
        args.evidence.mkdir(parents=True)
    started = time.monotonic()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(K2PairEditTests)
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        result = unittest.TextTestRunner(stream=captured, verbosity=2).run(suite)
    text = captured.getvalue()
    print(text, end="")
    if args.evidence is not None:
        K = K2PairEditTests
        (args.evidence / "verification.txt").write_text(text, encoding="utf-8")
        detail = [{k: v for k, v in row.items() if k != "program"} for row in K.rows]
        rot_observed = len(K.rot_control)
        on_edit = len(K.cycles_on_edit)
        collateral = len(K.cycles_collateral)
        collateral_cells = sorted({c["read_exec_cell"] for c in K.cycles_collateral})
        full_joint = [r for r in K.joint
                      if r["distinct_outcomes"] == len(STORAGE_DOMAIN)]
        rail_joint = [r for r in K.joint
                      if r["first"] in K.measured_states
                      and r["second"] in K.measured_states]
        best_rail = max(r["distinct_outcomes"] for r in rail_joint)
        echoed = [e for e in K.echoes if e["status"] == "stdin_byte_echoed"]
        cycles = [{"read_cell": c["read_cell"], "successor": c["successor"], "byte": c["byte"],
                   "op": c["op"], "store_cell": c["store_cell"], "old": c["old"],
                   "new": c["new"], "predicted": c["predicted"],
                   "matches": c["new"] == c["predicted"],
                   "depends_on_byte": c["depends_on_byte"],
                   "read_exec_cell": c["read_exec_cell"],
                   "store_exec_cell": c["store_exec_cell"], "step_gap": c["step_gap"],
                   "at_edited_cell": c["at_edited_cell"],
                   "store_at_edited_successor": c["store_at_edited_successor"]}
                  for c in K.cycles]
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
            "oracle_binaries_sha256": {f"<tmp>/{K.tracer.name}": K.tracer_sha256},
            "method": {
                "edit_set": "two cells: `/` at c, one letter at c+1, each mirrored at c+26414",
                "edit_value": "33 + ((xlat1_index(letter) - cell) % 94)",
                "pair_source": f"consecutive-step cell pairs from a {GEOMETRY_WINDOW}-step "
                               f"loop-phase trace of the unmodified candidate, at/after the "
                               f"loop-entry cell {LOOP_TRIGGER}",
                "successor_letters": SUCCESSORS,
                "screen_cap_steps": int(SCREEN_CAP), "full_run_cap_steps": int(FULL_CAP),
                "geometry_trace_steps": GEOMETRY_WINDOW,
                "per_run_trace_steps": RUN_WINDOW,
                "phase_trigger": f"-f {LOOP_TRIGGER} on every run; phase A = loader, "
                                 f"phase B = print loop",
                "store_detection": f"first p/* store executed within {MAX_STORE_GAP} STEPS of "
                                   f"an IN: step (traced lines are not steps); "
                                   f"immediate = exactly 1 step apart, and every event records "
                                   f"the cell the machine executed as well as the cell edited",
                "stdin": "byte 81 (`Q`, the branch discriminator) then bytes 40..119",
                "perturbation": f"byte at the position a traced read consumed replaced by "
                                f"{PROBE_BYTE}; the stored value must move and match "
                                f"crazy({PROBE_BYTE}, old)",
                "storage_domain": "bytes 0..255 plus 59048 (the EOF value `/` yields)",
                "census": "store_map() over all 59049 old values, checked against a direct "
                          "crazy_op evaluation on a stride-211 sample plus every measured "
                          "state and reservoir (mismatch list published)",
            },
            "baseline_full_run": K.full_baseline,
            "traced_geometry_steps": K.traced_steps,
            "adjacent_pairs": len(K.pairs),
            "adjacent_pair_visits": [
                {"cell": cell, "pair_steps": count, "edit_runs": len(SUCCESSORS)}
                for cell, count in sorted(K.pairs.items(), key=lambda kv: -kv[1])],
            "pair_runs": len(K.rows),
            "pair_runs_that_read_in_loop": len(K.reading_rows),
            "pair_runs_with_store_within_8_steps": len(
                [r for r in K.rows if r["stores_within_8_steps"]]),
            "pair_runs_with_immediate_store": len(K.cycle_rows),
            "cycles_on_the_edited_pair": len(K.cycles_on_edit),
            "cycles_on_the_edited_pair_cells": sorted({c["read_cell"]
                                                       for c in K.cycles_on_edit}),
            "cycles_collateral": len(K.cycles_collateral),
            "cycles_collateral_exec_cells": sorted({c["read_exec_cell"]
                                                    for c in K.cycles_collateral}),
            "confirmed_on_the_edited_pair": len(K.confirmed_on_edit),
            "edited_pair_immediate_store_letters": sorted(
                {c["successor"] for c in K.cycles + K.controls
                 if c["at_edited_cell"] and c["store_at_edited_successor"]}),
            "edited_pair_letters_without_store": sorted(
                {c["successor"] for c in K.rows
                 if c["cell"] in {r["read_cell"] for r in K.cycles_on_edit}
                 and not c["immediate_store"]}),
            "max_loop_reads": max(r["loop_reads"] for r in K.rows),
            "pair_run_detail": detail,
            "verified_read_store_cycles": cycles,
            "rot_successor_controls": [
                {"read_cell": c["read_cell"], "successor": c["successor"], "byte": c["byte"],
                 "store_cell": c["store_cell"], "old": c["old"], "new": c["new"],
                 "rot_of_old": c["predicted"], "depends_on_byte": c["depends_on_byte"]}
                for c in K.controls],
            "stdin_perturbation": K.perturbations,
            "stdin_perturbation_statuses": dict(Counter(p["status"] for p in K.perturbations)),
            "stdin_perturbation_confirmed": len(K.confirmed),
            "stdin_perturbation_rot_control": K.rot_control,
            "full_run_of_reading_pairs": K.full_rows,
            "max_loop_reads_full": max([f["loop_reads"] for f in K.full_rows] or [0]),
            "max_echo_run_any_pair": max(f["echo_run_of_stdin"] for f in K.full_rows),
            "stdin_byte_echo_probe": K.echoes,
            "stdin_byte_echo_statuses": dict(Counter(e["status"] for e in K.echoes)),
            "injectivity_census": {
                "cell_states_checked": N,
                "storage_domain_size": len(STORAGE_DOMAIN),
                "one_store_determines_the_byte": len(K.injective),
                "injective_states": K.injective,
                "max_candidates_per_observation": K.max_ambiguity,
                "histogram_bytes_collapsed_to_states": {str(k): v for k, v in
                                                        sorted(K.histogram.items())},
                "fast_vs_direct_mismatches": K.mismatch,
            },
            "measured_store_states": K.measured_states,
            "one_store_ambiguity": K.ambiguity,
            "same_cell_repeat": K.repeat,
            "two_bytes_one_cell": K.two_bytes_one_cell,
            "joint_two_cells": K.joint,
            "joint_two_cells_injective_rail_pairs": K.injective_rail_pairs,
            "joint_two_cells_full_range_pairings": len(full_joint),
            "joint_two_cells_measured_pairings": len(rail_joint),
            "joint_two_cells_measured_best_outcomes": best_rail,
            "claims": {
                f"a two-cell mirrored edit set can execute a read and a store one step "
                f"apart AT the two edited cells in the print loop ({on_edit} cycles, stored "
                f"value == crazy(byte, old))":
                    "DEMONSTRATED" if K.cycles_on_edit else "NOT_DEMONSTRATED",
                "the value stored at that edited pair moves with the stdin byte, shown by "
                "re-running the same program with a different byte "
                f"({len(K.confirmed_on_edit)} reproduced runs)":
                    "DEMONSTRATED" if K.confirmed_on_edit else "NOT_DEMONSTRATED",
                "the stored value depends on the stdin byte, across every immediate-store "
                f"run ({len(K.confirmed)} of {len(K.cycle_rows)} reproduced under the probe "
                f"byte)":
                    "DEMONSTRATED" if K.confirmed else "NOT_DEMONSTRATED",
                "`*` successors store, but their value is byte-independent: under the "
                f"probe byte every reproduced rot store kept exactly rot(old) "
                f"({rot_observed} runs)": "DEMONSTRATED",
                f"a read->store cycle can execute at cells the edit never touched: "
                f"{collateral} of {len(K.cycles)} ran at executed cells {collateral_cells}, "
                f"because a two-cell edit reroutes the trajectory onto read/store pairs the "
                f"quine image already contains (the other {on_edit} were on the edited pair)":
                    "DEMONSTRATED" if K.cycles_collateral else "NOT_DEMONSTRATED",
                f"one `p` store does NOT determine the byte "
                f"({len(K.injective)} of {N} cell states are injective, worst case "
                f"{K.max_ambiguity} candidate bytes for one observation)": "DEMONSTRATED",
                "a second store into the same cell never narrows the byte, and often "
                "widens it": "DEMONSTRATED",
                "two stores into DISTINCT cells can be jointly injective, but only with a "
                f"reservoir state: {len(full_joint)} of {len(K.joint)} pairings over the "
                f"measured states plus the three rot-fixed reservoirs reach all "
                f"{len(STORAGE_DOMAIN)} outcomes, every one of them containing 29524 or "
                "pairing 0 with 59048": "DEMONSTRATED",
                "no pairing of two ordinary cell states reached by a live run recovers the "
                f"byte (best of {len(rail_joint)} measured-measured pairings: {best_rail} "
                f"of {len(STORAGE_DOMAIN)} outcomes; the stage-N exception (82, 26400) was "
                "an artifact of mis-attributed events)": "DEMONSTRATED",
                "a program that performs that double store on one byte":
                    "NOT_DEMONSTRATED",
                "no two-cell edit set yields a byte-exact quine": "DEMONSTRATED",
                "no two-cell edit set echoes eight or more consecutive stdin bytes":
                    "DEMONSTRATED",
                f"the C branch CAN put a stdin byte on stdout: {len(echoed)} of "
                f"{len(K.echoes)} `<`-successor edit sets print the very byte their read "
                f"consumed, and the printed byte moves when that byte is replaced by "
                f"{PROBE_BYTE}":
                    "DEMONSTRATED" if echoed else "NOT_DEMONSTRATED",
                f"the echo is one byte long: the longest consecutive stdin run printed by "
                f"any of the {len(K.full_rows)} full runs is "
                f"{max(f['echo_run_of_stdin'] for f in K.full_rows)} bytes": "DEMONSTRATED",
                "the machine ever puts a loop-reachable cell into a 29524 reservoir state":
                    "NOT_DEMONSTRATED",
                "a read/store/restore cycle that keeps the QUINE row": "NOT_DEMONSTRATED",
                "an executable C-branch read/store loop": "NOT_DEMONSTRATED",
                "C echoes a RUN of stdin bytes (what the CAT row needs)":
                    "NOT_DEMONSTRATED",
                "single program satisfying both QUINE and CAT rows (K2)":
                    "NOT_DEMONSTRATED",
            },
            "not_demonstrated": [
                "a double store of one byte into two cells: the jointly injective state "
                "pairs were measured from SEPARATE programs, and no single run was made to "
                "hold both states at once",
                "that a reservoir-free pairing is impossible in general: joint injectivity "
                "was pair-tested over 4 states reached by a live cycle plus the 3 "
                "rot-fixed reservoirs (49 pairings), not over all 59,049 x 59,049 state "
                "pairs - the exhaustive census here covers SINGLE stores only",
                "that any loop-reachable cell can be routed to the 29524 reservoir state",
                "restoring the accumulator before the next `<` (none of the 7 successor "
                "letters tried produces a restore that survives to the next print)",
                "that the collateral cycles are CAUSED by the edit rather than merely "
                "exposed by it: the unmodified quine was not traced at those executed cells",
                "payload echo in the C branch", "executable K2",
                "two-engine parity for the pair programs (only the compiled tracer was run)",
                "more than one byte stored per read cycle",
                "an echo longer than one byte: the `<` successor reaches exactly the byte "
                "the read put in `a`, and nothing tried keeps a second byte alive to the "
                "next print",
                "the 6,221 cells outside the quine image hosting a cat loop"],
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
