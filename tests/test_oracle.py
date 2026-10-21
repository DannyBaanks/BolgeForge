"""CLI regressions: reject invalid sources and never confuse fuel with HALT."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORACLE = Path(os.environ.get('MB_REF', ROOT / 'mb_ref'))

class OracleTests(unittest.TestCase):
    def run_source(self, source, *args):
        with tempfile.NamedTemporaryFile() as program:
            program.write(source)
            program.flush()
            return subprocess.run([str(ORACLE), program.name, *args], input=b'', capture_output=True, timeout=3)

    def test_invalid_initial_opcode_rejected(self):
        result = self.run_source(b'!!', '1')
        self.assertEqual(result.returncode, 1)
        self.assertIn(b'INVALID_OPCODE', result.stderr)

    def test_too_short_rejected(self):
        for source in [b'', b' ', b'Q']:
            with self.subTest(source=source):
                result = self.run_source(source, '1')
                self.assertEqual(result.returncode, 1)
                self.assertIn(b'TOO_SHORT', result.stderr)

    def test_halt_is_the_only_success(self):
        self.assertEqual(self.run_source(b'QC', '1').returncode, 0)
        result = self.run_source(b'QC', '0')
        self.assertEqual(result.returncode, 2)
        self.assertIn(b'MAX_STEPS', result.stderr)
        self.assertEqual(self.run_source(b'DP', '1').returncode, 2)
        self.assertEqual(self.run_source(b'DP', '2').returncode, 0)

    def test_budget_must_be_unsigned_integer(self):
        for budget in ['-1', 'abc', '1x', '', '18446744073709551616']:
            with self.subTest(budget=budget):
                self.assertEqual(self.run_source(b'QC', budget).returncode, 1)

    def test_excess_arguments_rejected(self):
        self.assertEqual(self.run_source(b'QC', '1', 'extra').returncode, 1)

    def test_invalid_bytes_and_oversize_rejected(self):
        self.assertEqual(self.run_source(b'QC\x00', '1').returncode, 1)
        # Whitespace is ignored, but all non-whitespace cells count.
        source = bytes(33 + (35 - i) % 94 for i in range(59050))
        result = self.run_source(source, '1')
        self.assertEqual(result.returncode, 1)
        self.assertIn(b'too long', result.stderr)

    def test_runtime_nonprintable_is_never_skipped_or_indexed(self):
        for source, tag in [(b"('", b'NONPRINTABLE_PC'), (b"b'", b'INVALID_ENCRYPTION')]:
            with self.subTest(source=source):
                result = self.run_source(source, '100')
                self.assertEqual(result.returncode, 3)
                self.assertIn(tag, result.stderr)

    def test_whitespace_does_not_change_instruction_addresses(self):
        self.assertEqual(self.run_source(b'\tQ\n C\r', '1').returncode, 0)

    def test_experimental_programs_cannot_be_certified_as_classic(self):
        for name in ['microcat.mal', 'truth_machine.mal', 'fizzbuzz.mal',
                     'cand_three_stage_clean.mal', 'cand_twostroke.mal']:
            with self.subTest(name=name):
                result = subprocess.run([str(ORACLE), str(ROOT / 'artifacts' / name), '20000'],
                                        input=b'1', capture_output=True, timeout=3)
                self.assertEqual(result.returncode, 1)
                self.assertIn(b'INVALID_OPCODE', result.stderr)

if __name__ == '__main__':
    unittest.main()
