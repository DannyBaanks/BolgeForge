"""Controls for the handoff-state gate that guards suffix-shifted Malbolge programs."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.verify_handoff_state import MEM_SIZE, compare_handoff  # noqa: E402

DELTA = 100
FLOOR = 100
CEILING = 60_000
IMAGE = 12
VAR_A, VAR_B = 50_000, 50_001


def build_shift_all(variables, *, ref_d=50_500, cand_d=50_400, cand_cell=900, cand_values=None):
    """Reference/candidate pair laid out the way the 2026-10-19 pilot assumed."""
    ref_init = [0] * MEM_SIZE
    ref_mem = [0] * MEM_SIZE
    cand_mem = [0] * MEM_SIZE
    for addr, value in variables.items():
        ref_mem[addr] = value
    cand_values = (
        {addr - DELTA: (value - DELTA if value >= FLOOR else value) for addr, value in variables.items()}
        if cand_values is None
        else cand_values
    )
    for addr, value in cand_values.items():
        cand_mem[addr] = value
    return compare_handoff(
        reference_mem=ref_mem,
        reference_init=ref_init,
        reference_cells=IMAGE,
        candidate_mem=cand_mem,
        candidate_cells=IMAGE,
        delta=DELTA,
        reference_cell=1000,
        candidate_cell=cand_cell,
        reference_regs=(7, ref_d),
        candidate_regs=(7, cand_d),
        value_floor=FLOOR,
        memory_mode="shift-all",
    )


def build_keep_high(variables, *, ref_d=50_500, cand_d=None, cand_cell=900, cand_values=None):
    """Reference/candidate pair laid out the way tools/resynthesize.py lays it out."""
    ref_init = [0] * MEM_SIZE
    ref_mem = [0] * MEM_SIZE
    cand_mem = [0] * MEM_SIZE
    for addr, value in variables.items():
        ref_mem[addr] = value
    cand_values = (
        {addr: (value - DELTA if FLOOR < value < CEILING else value) for addr, value in variables.items()}
        if cand_values is None
        else cand_values
    )
    for addr, value in cand_values.items():
        cand_mem[addr] = value
    return compare_handoff(
        reference_mem=ref_mem,
        reference_init=ref_init,
        reference_cells=IMAGE,
        candidate_mem=cand_mem,
        candidate_cells=IMAGE,
        delta=DELTA,
        reference_cell=1000,
        candidate_cell=cand_cell,
        reference_regs=(7, ref_d),
        candidate_regs=(7, ref_d if cand_d is None else cand_d),
        value_floor=FLOOR,
        value_ceiling=CEILING,
        memory_mode="keep-high",
    )


class ShiftAllModelTests(unittest.TestCase):
    def test_matching_state_passes(self):
        report = build_shift_all({VAR_A: 90, VAR_B: 7_500})
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["variables_installed"], 2)
        self.assertEqual(report["variables_wrong"], 0)

    def test_unshifted_variable_fails(self):
        report = build_shift_all({VAR_A: 7_500}, cand_values={VAR_A - DELTA: 7_500})
        self.assertFalse(report["ok"])
        self.assertEqual(report["variables_wrong"], 1)
        self.assertEqual(report["mismatches"][0]["cell"], VAR_A - DELTA)
        self.assertEqual(report["mismatches"][0]["expected"], 7_400)
        self.assertEqual(report["mismatches"][0]["actual"], 7_500)

    def test_missing_variable_fails(self):
        report = build_shift_all({VAR_A: 90}, cand_values={})
        self.assertFalse(report["ok"])
        self.assertEqual(report["variables_installed"], 0)
        self.assertEqual(report["mismatches"][0]["reason"], f"variable from cell {VAR_A}")

    def test_register_d_mismatch_fails(self):
        report = build_shift_all({VAR_A: 90}, cand_d=97)
        self.assertFalse(report["ok"])
        self.assertEqual(report["register_mismatches"], [{"register": "d", "reference": 50_400, "candidate": 97}])

    def test_wrong_entry_cell_fails(self):
        report = build_shift_all({VAR_A: 90}, cand_cell=901)
        self.assertFalse(report["ok"])
        self.assertEqual(report["mismatches"][0]["reason"], "program counter")

    def test_value_floor_boundary(self):
        at_floor = build_shift_all({VAR_A: FLOOR}, cand_values={VAR_A - DELTA: FLOOR - DELTA})
        self.assertTrue(at_floor["ok"], "a value equal to the floor must be shifted")
        below_floor = build_shift_all({VAR_A: FLOOR - 1}, cand_values={VAR_A - DELTA: FLOOR - 1})
        self.assertTrue(below_floor["ok"], "a value below the floor must not be shifted")


class KeepHighModelTests(unittest.TestCase):
    def test_matching_state_passes(self):
        report = build_keep_high({VAR_A: 90, VAR_B: 7_500})
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["variables_installed"], 2)
        self.assertEqual(report["register_mismatches"], [])

    def test_register_d_is_not_shifted(self):
        report = build_keep_high({VAR_A: 90}, cand_d=50_400)
        self.assertFalse(report["ok"])
        self.assertEqual(report["register_mismatches"], [{"register": "d", "reference": 50_500, "candidate": 50_400}])

    def test_variable_stays_at_original_address(self):
        report = build_keep_high({VAR_A: 90})
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["mismatches"], [])

    def test_shifted_address_value_is_decremented(self):
        report = build_keep_high({VAR_A: 7_500}, cand_values={VAR_A: 7_500})
        self.assertFalse(report["ok"])
        self.assertEqual(report["mismatches"][0]["cell"], VAR_A)
        self.assertEqual(report["mismatches"][0]["expected"], 7_400)

    def test_band_boundaries_are_exclusive(self):
        at_floor = build_keep_high({VAR_A: FLOOR}, cand_values={VAR_A: FLOOR})
        self.assertTrue(at_floor["ok"], "the floor itself is outside the shifted band")
        at_ceiling = build_keep_high({VAR_A: CEILING}, cand_values={VAR_A: CEILING})
        self.assertTrue(at_ceiling["ok"], "the ceiling itself is outside the shifted band")

    def test_unknown_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            compare_handoff(
                reference_mem=[0] * MEM_SIZE,
                reference_init=[0] * MEM_SIZE,
                reference_cells=IMAGE,
                candidate_mem=[0] * MEM_SIZE,
                candidate_cells=IMAGE,
                delta=DELTA,
                reference_cell=1000,
                candidate_cell=900,
                reference_regs=(0, 0),
                candidate_regs=(0, 0),
                value_floor=FLOOR,
                memory_mode="bogus",
            )


class PublishedArtifactControls(unittest.TestCase):
    """The gate must accept the verified artifact and reject the broken pilot.

    These controls are what make the gate trustworthy: a gate that fails the
    published, byte-exact ``cat_compressed.mal`` is measuring the wrong layout.
    """

    def run_gate(self, *args):
        from tools.verify_handoff_state import main
        return main([str(a) for a in args])

    def test_cat_compressed_matches_keep_high(self):
        code = self.run_gate(
            "--reference", ROOT / "reference" / "malbolge_org" / "cat.mal",
            "--reference-cell", 9067,
            "--candidate", ROOT / "artifacts" / "cat_compressed.mal",
            "--delta", 1128,
            "--value-floor", 9003,
        )
        self.assertEqual(code, 0, "cat_compressed.mal must satisfy the keep-high handoff")

    def test_cat_compressed_fails_shift_all(self):
        code = self.run_gate(
            "--reference", ROOT / "reference" / "malbolge_org" / "cat.mal",
            "--reference-cell", 9067,
            "--candidate", ROOT / "artifacts" / "cat_compressed.mal",
            "--delta", 1128,
            "--memory-mode", "shift-all",
        )
        self.assertEqual(code, 1, "the shift-all layout does not describe cat_compressed.mal")

    def test_keep_high_requires_value_floor(self):
        code = self.run_gate(
            "--reference", ROOT / "reference" / "malbolge_org" / "cat.mal",
            "--reference-cell", 9067,
            "--candidate", ROOT / "artifacts" / "cat_compressed.mal",
            "--delta", 1128,
        )
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
