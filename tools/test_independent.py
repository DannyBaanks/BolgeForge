#!/usr/bin/env python3
"""Differential checks against the pinned, unmodified Olmstead audit mirror.

Only known loader-valid programs are executed; malformed/short sources never
reach the historical interpreter's unsafe memory initialization paths.
"""
import hashlib
import os
import random
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/audits/2026-10-20-e2e/olmstead_strict_mirror.c'
ORACLE = Path(os.environ.get('MB_REF', ROOT / ('mb_ref.exe' if os.name == 'nt' else 'mb_ref')))


def _find_cc():
    for name in ('cc', 'gcc', 'clang'):
        found = shutil.which(name)
        if found:
            return found
    raise RuntimeError('No C compiler found (cc/gcc/clang); install gcc/MinGW on Windows or gcc on Linux')


def _mirror_source_for_build(directory):
    """Return the mirror source to compile.

    The pinned audit mirror in docs/ is never modified. On Windows the
    historical interpreter needs binary stdin/stdout (and "rb" for the
    program file); that patch is applied only to a temporary copy.
    On Linux/macOS the pinned source is compiled as-is.
    """
    if os.name != 'nt':
        return SOURCE
    # Normalize CRLF/LF first: the Windows working tree has CRLF, the
    # git blob has LF, and the replacements below must match either.
    text = SOURCE.read_bytes().decode('utf-8').replace('\r\n', '\n')
    patched = text.replace(
        '#include <string.h>',
        '#include <string.h>\n#include <fcntl.h>\n#include <io.h>', 1)
    # Inject after the declarations in main() (C89-style block), not
    # before them, so the patched copy stays declaration-first.
    patched = patched.replace(
        'unsigned short *mem;\n',
        'unsigned short *mem;\n'
        '  _setmode(_fileno(stdin), _O_BINARY);\n'
        '  _setmode(_fileno(stdout), _O_BINARY);\n', 1)
    patched = patched.replace('fopen( argv[1], "r" )', 'fopen( argv[1], "rb" )', 1)
    if '_setmode' not in patched or '"rb"' not in patched:
        raise RuntimeError('Windows mirror patch did not apply; mirror source changed?')
    out = Path(directory) / 'olmstead_mirror_win.c'
    out.write_bytes(patched.encode('utf-8'))
    return out


def execute(binary, program, payload):
    result = subprocess.run([str(binary), str(program)], input=payload,
                            capture_output=True, timeout=20)
    if result.returncode or result.stderr:
        raise RuntimeError(f'{program.name}: independent execution failed ({result.returncode})')
    return result.stdout


def main():
    with tempfile.TemporaryDirectory(prefix='bolgeforge-independent-') as directory:
        binary = Path(directory) / ('olmstead.exe' if os.name == 'nt' else 'olmstead')
        mirror = _mirror_source_for_build(directory)
        subprocess.run([_find_cc(), '-O2', '-o', str(binary), str(mirror)], check=True)
        cases = []
        for folder in ['reference/malbolge_org', 'artifacts']:
            for program in sorted((ROOT / folder).glob('*.mal')):
                if folder == 'artifacts' and not (
                    program.name.startswith('candidate_m')
                    or program.name.endswith('_compressed.mal')
                    or program.name == 'cat_compact.mal'
                ):
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
        # The compact Cat is a separate artifact (not one of the four rebuilt benchmarks);
        # give it the same streaming battery as the compressed Cat.
        compact = ROOT / 'artifacts' / 'cat_compact.mal'
        if not compact.is_file():
            raise RuntimeError(f'Required artifact missing: {compact}')
        rng = random.Random(2026)
        for payload in (b'', b'ABCD', bytes(range(256)) * 16,
                        bytes(rng.randrange(256) for _ in range(65_536))):
            cases.append((compact, payload))
        for program, payload in cases:
            expected = execute(ORACLE, program, payload)
            actual = execute(binary, program, payload)
            if actual != expected:
                raise RuntimeError(f'Independent mismatch: {program.name}, input {payload[:40]!r}')
            if program.name.startswith('candidate_m') and actual != program.read_bytes():
                raise RuntimeError(f'Independent quine mismatch: {program.name}')
        print(f'PASS independent Olmstead mirror: {len(cases)} exact-output comparisons')
        print(f'Mirror source SHA-256: {hashlib.sha256(SOURCE.read_bytes()).hexdigest()}')


if __name__ == '__main__':
    main()
