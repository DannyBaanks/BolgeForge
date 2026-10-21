"""Loader-valid FizzBuzz reference (angel_p_57), empty stdin, exact 100 lines.

The preserved conversion reads stdin 109 times and treats EOF as the constant
59048. With empty stdin those reads terminate immediately; this test therefore
certifies *loader validity, output and HALT*, not zero-read behaviour or any
historical primacy claim.
"""
import hashlib
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORACLE = Path(os.environ.get('MB_REF', ROOT / 'mb_ref'))
REFERENCE = ROOT / 'docs/audits/2026-10-20-e2e/angel_fizzbuzz_converted.mal'
EXPECTED_SHA256 = 'f039dc221ad122dda8b7226ad5bc68b8654e9e3a42dcea2b37554cd6f91b56af'


def expected_output():
    lines = []
    for value in range(1, 101):
        if value % 15 == 0:
            lines.append('FizzBuzz')
        elif value % 3 == 0:
            lines.append('Fizz')
        elif value % 5 == 0:
            lines.append('Buzz')
        else:
            lines.append(str(value))
    return ''.join(line + '\n' for line in lines).encode()


class FizzBuzzReferenceTests(unittest.TestCase):
    def test_strict_loader_accepts_reference(self):
        result = subprocess.run([str(ORACLE), str(REFERENCE), '1'], input=b'', capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(b'INVALID_OPCODE', result.stderr)

    def test_empty_stdin_halts_with_exact_100_lines(self):
        result = subprocess.run(
            [str(ORACLE), str(REFERENCE), '100000000'],
            input=b'', capture_output=True, timeout=120,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, b'')
        self.assertEqual(result.stdout, expected_output())
        self.assertEqual(len(result.stdout.splitlines()), 100)
        self.assertEqual(hashlib.sha256(result.stdout).hexdigest(), EXPECTED_SHA256)

    def test_old_fizzbuzz_is_rejected_by_strict_loader(self):
        old = ROOT / 'artifacts/fizzbuzz.mal'
        result = subprocess.run([str(ORACLE), str(old), '10'], input=b'', capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b'INVALID_OPCODE', result.stderr)


if __name__ == '__main__':
    unittest.main()
