#!/usr/bin/env python3
"""Strict, bounded, exact-output checks; missing artifacts are failures."""
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MB_REF = REPO_ROOT / 'mb_ref'
ARTIFACTS = REPO_ROOT / 'artifacts'
REFERENCE = REPO_ROOT / 'reference' / 'malbolge_org'
TARGETS = ('cat', 'digital_root', 'adder', '99_bottles')


def run(program, payload=b''):
    result = subprocess.run([str(MB_REF), str(program), '100000000'], input=payload,
                            capture_output=True, timeout=20)
    if result.returncode != 0 or result.stderr:
        raise RuntimeError(f'{program.name}: exit={result.returncode}, {result.stderr!r}')
    return result.stdout


def verify_target(name, program):
    """Returns checked case count. Reference parity also needs semantic expectations."""
    original = REFERENCE / f'{name}.mal'
    if not program.is_file() or not original.is_file():
        raise FileNotFoundError(f'Required artifact/reference missing: {name}')
    if name == 'cat':
        payloads = [b'', b'A', b'ABC', b'ABCD', b'Hello BolgeForge\n',
                    bytes(range(256)), bytes(range(256)) * 16]
        cases = [(payload, payload) for payload in payloads]
    elif name == 'digital_root':
        cases = [(b'0\n', b'0\n'), (b'9\n', b'9\n'), (b'10\n', b'1\n'),
                 (b'42\n', b'6\n'), (b'12345\n', b'6\n'), (b'987654321\n', b'9\n')]
    elif name == 'adder':
        # Author's domain: each operand is 0..999, separated by a space.
        values = (0, 1, 2, 9, 10, 99, 100, 499, 998, 999)
        cases = [(f'{a} {b}\n'.encode(), f'{a+b}\n'.encode()) for a in values for b in values]
    elif name == '99_bottles':
        expected = run(original)
        if len(expected) != 11459:
            raise RuntimeError('Reference lyrics length changed')
        cases = [(b'', expected)]
    else:
        raise ValueError(name)
    for payload, expected in cases:
        actual = run(program, payload)
        if actual != expected or run(original, payload) != expected:
            raise RuntimeError(f'{name}: mismatch for {payload[:40]!r}; received {actual[:80]!r}')
    return len(cases)


def test_compressed():
    # Check the entire inventory before any success messages.
    for name in TARGETS:
        if not (ARTIFACTS / f'{name}_compressed.mal').is_file():
            raise FileNotFoundError(f'Required artifact missing: {name}_compressed.mal')
    for name in TARGETS:
        count = verify_target(name, ARTIFACTS / f'{name}_compressed.mal')
        print(f'PASS {name}: {count} exact-output cases; strict HALT and reference parity')


if __name__ == '__main__':
    test_compressed()
