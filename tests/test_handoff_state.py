"""Controls for the handoff-state gate that guards suffix-shifted Malbolge programs."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.verify_handoff_state import MEM_SIZE, compare_handoff  # noqa: E402

DELTA = 100
FLOOR = 100
IMAGE = 12
VAR_A, VAR_B = 50_000, 50_001


def build(variables, *, ref_d=50_500, cand_d=50_400, cand_cell=900, cand_values=None):
    """Build a reference/candidate pair with explicit handoff states."""
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
    )


class HandoffGateTests(unittest.TestCase):
    def test_matching_state_passes(self):
        report = build({VAR_A: 90, VAR_B: 7_500})
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["variables_installed"], 2)
        self.assertEqual(report["variables_wrong"], 0)

    def test_unshifted_variable_fails(self):
        report = build({VAR_A: 7_500}, cand_values={VAR_A - DELTA: 7_500})
        self.assertFalse(report["ok"])
        self.assertEqual(report["variables_wrong"], 1)
        self.assertEqual(report["mismatches"][0]["cell"], VAR_A - DELTA)
        self.assertEqual(report["mismatches"][0]["expected"], 7_400)
        self.assertEqual(report["mismatches"][0]["actual"], 7_500)

    def test_missing_variable_fails(self):
        report = build({VAR_A: 90}, cand_values={})
        self.assertFalse(report["ok"])
        self.assertEqual(report["variables_installed"], 0)
        self.assertEqual(report["mismatches"][0]["reason"], f"variable from cell {VAR_A}")

    def test_register_d_mismatch_fails(self):
        report = build({VAR_A: 90}, cand_d=97)
        self.assertFalse(report["ok"])
        self.assertEqual(report["register_mismatches"], [{"register": "d", "reference": 50_400, "candidate": 97}])

    def test_wrong_entry_cell_fails(self):
        report = build({VAR_A: 90}, cand_cell=901)
        self.assertFalse(report["ok"])
        self.assertEqual(report["mismatches"][0]["reason"], "program counter")

    def test_value_floor_boundary(self):
        at_floor = build({VAR_A: FLOOR}, cand_values={VAR_A - DELTA: FLOOR - DELTA})
        self.assertTrue(at_floor["ok"], "a value equal to the floor must be shifted")
        below_floor = build({VAR_A: FLOOR - 1}, cand_values={VAR_A - DELTA: FLOOR - 1})
        self.assertTrue(below_floor["ok"], "a value below the floor must not be shifted")


if __name__ == "__main__":
    unittest.main()
