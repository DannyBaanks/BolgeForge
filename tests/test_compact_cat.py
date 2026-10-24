"""Certification for artifacts/cat_compact.mal (7,972 cells, k=15 plan)."""
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_compact_cat import OUT_PATH, build, handoff_report  # noqa: E402
from tools.test_compressed import REFERENCE, run, verify_target  # noqa: E402

CAT_COMPRESSED = ROOT / "artifacts" / "cat_compressed.mal"


class CompactCatTests(unittest.TestCase):
    def test_artifact_is_smaller_than_the_published_cat(self):
        self.assertTrue(OUT_PATH.is_file(), "artifacts/cat_compact.mal is missing")
        cells = [b for b in OUT_PATH.read_bytes() if 33 <= b <= 126]
        compressed = [b for b in CAT_COMPRESSED.read_bytes() if 33 <= b <= 126]
        self.assertEqual(len(cells), 7_972)
        self.assertLess(len(cells), len(compressed))
        self.assertEqual(len(compressed), 8_254)

    def test_deterministic_rebuild_matches(self):
        raw, info = build()
        self.assertEqual(OUT_PATH.read_bytes(), raw)
        self.assertEqual(info["plan"], {"k": 15, "seed": 47, "borrow_penalty": 2, "direct_gap": 9})
        self.assertEqual(info["preamble_ops"], 7_443)
        self.assertLessEqual(info["end_c"], info["handoff_cell"])

    def test_exact_output_battery(self):
        self.assertEqual(verify_target("cat", OUT_PATH), 7)

    def test_long_binary_stream_matches_reference(self):
        rng = random.Random(2026)
        payload = bytes(rng.randrange(256) for _ in range(65_536))
        self.assertEqual(run(OUT_PATH, payload), run(REFERENCE / "cat.mal", payload))

    def test_handoff_state_matches_reference(self):
        report = handoff_report(OUT_PATH.read_bytes())
        self.assertTrue(report["ok"], report["mismatches"][:3])
        self.assertEqual(report["variables_installed"], report["variables_total"])
        self.assertEqual(report["variables_total"], 124)
        self.assertEqual(report["register_mismatches"], [])


if __name__ == "__main__":
    unittest.main()
