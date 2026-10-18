#!/usr/bin/env python3
"""test_corpus.py - Test runner for the malbolge.org reference corpus in BolgeForge.

Verifies execution and correctness of all programs from malbolge.org against
the independent C oracle `mb_ref` (Olmstead Classic semantics).
"""
import sys
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
MB_REF = REPO_ROOT / 'mb_ref'
CORPUS_DIR = REPO_ROOT / 'reference' / 'malbolge_org'


def run_prog(prog_path: Path, stdin_text: str = '') -> str:
    res = subprocess.run(
        [str(MB_REF), str(prog_path)],
        input=stdin_text.encode('latin1'),
        capture_output=True,
        check=True
    )
    return res.stdout.decode('latin1')


def test_cat():
    print("Testing cat.mal...", end=" ", flush=True)
    prog = CORPUS_DIR / 'cat.mal'
    vectors = [
        "Hello, Malbolge!\n",
        "12345\n",
        "BolgeForge beats Lutter 2026\n",
    ]
    for v in vectors:
        out = run_prog(prog, v)
        assert out == v, f"cat mismatch: expected {v!r}, got {out!r}"
    print("PASS")


def test_digital_root():
    print("Testing digital_root.mal...", end=" ", flush=True)
    prog = CORPUS_DIR / 'digital_root.mal'
    vectors = [
        ("42\n", "6\n"),
        ("99\n", "9\n"),
        ("12345\n", "6\n"),
        ("7\n", "7\n"),
        ("999\n", "9\n"),
    ]
    for inp, expected in vectors:
        out = run_prog(prog, inp)
        assert out == expected, f"digital_root mismatch on {inp!r}: expected {expected!r}, got {out!r}"
    print("PASS")


def test_adder():
    print("Testing adder.mal...", end=" ", flush=True)
    prog = CORPUS_DIR / 'adder.mal'
    vectors = [
        ("12\n34\n", "46\n"),
        ("999\n1\n", "1000\n"),
        ("0\n0\n", "0\n"),
        ("123\n456\n", "579\n"),
    ]
    for inp, expected in vectors:
        out = run_prog(prog, inp)
        assert out == expected, f"adder mismatch on {inp!r}: expected {expected!r}, got {out!r}"
    print("PASS")


def test_quines():
    for name in ['quine.mal', 'quine-2012.mal']:
        print(f"Testing {name} self-reproduction...", end=" ", flush=True)
        prog = CORPUS_DIR / name
        expected = prog.read_bytes()
        res = subprocess.run([str(MB_REF), str(prog)], capture_output=True)
        assert res.returncode == 0, f"Non-zero exit code: {res.returncode}"
        assert res.stdout == expected, f"Quine mismatch for {name}: {len(res.stdout)} vs {len(expected)} bytes"
        print("PASS (0-byte diff bit-for-bit)")


def main():
    if not MB_REF.exists():
        print(f"ERROR: {MB_REF} not found. Run `make` first to build the oracle.", file=sys.stderr)
        sys.exit(1)

    t0 = time.time()
    print("=== RUNNING MALBOLGE.ORG REFERENCE CORPUS VERIFICATION ===")
    test_cat()
    test_digital_root()
    test_adder()
    test_quines()
    elapsed = time.time() - t0
    print(f"=== ALL MALBOLGE.ORG CORPUS TESTS PASSED ({elapsed:.2f}s) ===")


if __name__ == '__main__':
    main()
