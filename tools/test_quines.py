#!/usr/bin/env python3
"""Verify the complete committed quine inventory; any failure propagates."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ('candidate_m281_53562b.mal', 'candidate_m284_54134b.mal',
            'candidate_m287_54706b.mal', 'candidate_m293_55850b.mal',
            'candidate_m308_58709b.mal')


def verify_quines(root=ROOT):
    artifacts = root / 'artifacts'
    for name in EXPECTED:
        if not (artifacts / name).is_file():
            raise FileNotFoundError(f'Required quine missing: {name}')
    for program in sorted(artifacts.glob('candidate_m*.mal')):
        result = subprocess.run([str(root / 'mb_ref'), str(program), '100000000'],
                                input=b'', capture_output=True, timeout=20)
        if result.returncode or result.stderr or result.stdout != program.read_bytes():
            raise RuntimeError(f'Quine mismatch: {program.name}, exit={result.returncode}')
        print(f'PASS {program.name}: byte-exact self-reproduction and strict HALT')


if __name__ == '__main__':
    verify_quines()
