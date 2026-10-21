#!/usr/bin/env python3
"""Differential checks against the pinned, unmodified Olmstead audit mirror.

Only known loader-valid programs are executed; malformed/short sources never
reach the historical interpreter's unsafe memory initialization paths.
"""
import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/audits/2026-10-20-e2e/olmstead_strict_mirror.c'


def execute(binary, program, payload):
    result = subprocess.run([str(binary), str(program)], input=payload,
                            capture_output=True, timeout=20)
    if result.returncode or result.stderr:
        raise RuntimeError(f'{program.name}: independent execution failed ({result.returncode})')
    return result.stdout


def main():
    with tempfile.TemporaryDirectory(prefix='bolgeforge-independent-') as directory:
        binary = Path(directory) / 'olmstead'
        subprocess.run(['cc', '-O2', '-o', str(binary), str(SOURCE)], check=True)
        cases = []
        for folder in ['reference/malbolge_org', 'artifacts']:
            for program in sorted((ROOT / folder).glob('*.mal')):
                if folder == 'artifacts' and not (program.name.startswith('candidate_m') or program.name.endswith('_compressed.mal')):
                    continue
                payload = b'12 34\n' if 'adder' in program.name else b'123\n'
                if 'quine' in program.name or 'candidate_m' in program.name or 'bottles' in program.name:
                    payload = b''
                cases.append((program, payload))
        # Binary stream, decimal edges and the author's complete finite sample domain.
        for name, payloads in [
            ('cat', [b'', b'ABCD', bytes(range(256)) * 16]),
            ('digital_root', [b'0\n', b'9\n', b'12345\n', b'987654321\n']),
            ('adder', [f'{a} {b}\n'.encode() for a in (0, 1, 2, 9, 10, 99, 100, 499, 998, 999)
                       for b in (0, 1, 2, 9, 10, 99, 100, 499, 998, 999)])]:
            for folder, suffix in [('reference/malbolge_org', ''), ('artifacts', '_compressed')]:
                cases.extend((ROOT / folder / f'{name}{suffix}.mal', payload) for payload in payloads)
        for program, payload in cases:
            expected = execute(ROOT / 'mb_ref', program, payload)
            actual = execute(binary, program, payload)
            if actual != expected:
                raise RuntimeError(f'Independent mismatch: {program.name}, input {payload[:40]!r}')
            if program.name.startswith('candidate_m') and actual != program.read_bytes():
                raise RuntimeError(f'Independent quine mismatch: {program.name}')
        print(f'PASS independent Olmstead mirror: {len(cases)} exact-output comparisons')
        print(f'Mirror source SHA-256: {hashlib.sha256(SOURCE.read_bytes()).hexdigest()}')


if __name__ == '__main__':
    main()
