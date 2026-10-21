"""Strict Classic streaming Cat: arbitrary binary payloads through 64 KiB."""
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORACLE = Path(os.environ.get('MB_REF', ROOT / 'mb_ref'))
CANDIDATES = [
    ROOT / 'artifacts/cat_compressed.mal',
    ROOT / 'reference/malbolge_org/cat.mal',
]


def payload(size=65536):
    return bytes(((i * 197 + 43) ^ (i >> 8)) & 0xFF for i in range(size))


class StreamingCatTests(unittest.TestCase):
    def run_cat(self, program, data):
        return subprocess.run(
            [str(ORACLE), str(program), '200000000'],
            input=data, capture_output=True, timeout=120,
        )

    def test_strict_loader_accepts_cats(self):
        for program in CANDIDATES:
            with self.subTest(program=program.name):
                result = self.run_cat(program, b'')
                self.assertNotEqual(result.returncode, 1)
                self.assertNotIn(b'INVALID_OPCODE', result.stderr)

    def test_empty_input_empty_output_halt(self):
        for program in CANDIDATES:
            with self.subTest(program=program.name):
                result = self.run_cat(program, b'')
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, b'')

    def test_all_256_bytes(self):
        data = bytes(range(256))
        for program in CANDIDATES:
            with self.subTest(program=program.name):
                result = self.run_cat(program, data)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, data)

    def test_64kib_binary_stream(self):
        data = payload()
        for program in CANDIDATES:
            with self.subTest(program=program.name):
                result = self.run_cat(program, data)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, data)
                self.assertEqual(result.stderr, b'')


if __name__ == '__main__':
    unittest.main()
