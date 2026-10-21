"""Strict-classic truth machine: loader, branches and full-state cycle proof."""
import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORACLE = Path(os.environ.get('MB_REF', ROOT / 'mb_ref'))
ARTIFACT = ROOT / 'artifacts/truth_machine_classic_90b.mal'
PROVER = ROOT / 'tools/prove_truth_machine.py'


class TruthMachineStrictTests(unittest.TestCase):
    def run_oracle(self, payload, budget):
        return subprocess.run(
            [str(ORACLE), str(ARTIFACT), str(budget)],
            input=payload, capture_output=True, timeout=60,
        )

    def test_strict_loader_accepts_artifact(self):
        result = self.run_oracle(b'', '1')
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(b'INVALID_OPCODE', result.stderr)

    def test_zero_prints_one_zero_and_halts(self):
        result = self.run_oracle(b'0', '10000')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b'0')
        self.assertEqual(result.stderr, b'')

    def test_one_prefix_is_all_ones(self):
        result = self.run_oracle(b'1', '1408')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(len(result.stdout), 58)
        self.assertEqual(set(result.stdout), {0x31})

    def test_old_truth_machine_is_rejected(self):
        old = ROOT / 'artifacts/truth_machine.mal'
        result = subprocess.run([str(ORACLE), str(old), '10'], input=b'0', capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b'INVALID_OPCODE', result.stderr)

    def test_cycle_proof(self):
        result = subprocess.run(
            ['python3', str(PROVER), str(ARTIFACT), '--json'],
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['verdict'], 'DEMONSTRATED')
        self.assertEqual(report['loader'], 'ACCEPT')
        self.assertEqual(report['branch_zero']['status'], 'HALT')
        self.assertEqual(report['branch_zero']['output_hex'], '30')
        self.assertEqual(report['branch_one']['status'], 'CYCLE')
        self.assertEqual(report['branch_one']['period'], 408)
        self.assertEqual(report['branch_one']['outputs_per_cycle'], 17)
        self.assertEqual(report['branch_one']['first_output_hex'], '31')


if __name__ == '__main__':
    unittest.main()
