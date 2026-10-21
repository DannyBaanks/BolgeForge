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


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run_prog(prog_path: Path, stdin_text: str = '') -> str:
    res = subprocess.run(
        [str(MB_REF), str(prog_path)],
        input=stdin_text.encode('latin1'),
        capture_output=True,
        check=True,
        timeout=20
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
        require(out == v, f"cat mismatch: expected {v!r}, got {out!r}")
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
        require(out == expected, f"digital_root mismatch on {inp!r}: expected {expected!r}, got {out!r}")
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
        require(out == expected, f"adder mismatch on {inp!r}: expected {expected!r}, got {out!r}")
    print("PASS")


def test_quines():
    for name in ['quine.mal', 'quine-2012.mal']:
        print(f"Testing {name} self-reproduction...", end=" ", flush=True)
        prog = CORPUS_DIR / name
        expected = prog.read_bytes()
        res = subprocess.run([str(MB_REF), str(prog)], input=b'', capture_output=True, timeout=20)
        require(res.returncode == 0, f"Non-zero exit code: {res.returncode}")
        require(res.stdout == expected, f"Quine mismatch for {name}: {len(res.stdout)} vs {len(expected)} bytes")
        print("PASS (0-byte diff bit-for-bit)")


def test_hello_world():
    print("Testing hello_world.mal...", end=" ", flush=True)
    prog = CORPUS_DIR / 'hello_world.mal'
    out = run_prog(prog)
    require(out == "Hello, world.", f"hello_world mismatch: got {out!r}")
    print("PASS")


def test_rot13():
    print("Testing rot13.mal...", end=" ", flush=True)
    prog = CORPUS_DIR / 'rot13.mal'
    vectors = [
        ("Hello, World!\n", "Uryyb, Jbeyq!\n"),
        ("Malbolge 2026\n", "Znyobytr 2026\n"),
        ("The Quick Brown Fox Jumps Over The Lazy Dog.\n", "Gur Dhvpx Oebja Sbk Whzcf Bire Gur Ynml Qbt.\n"),
    ]
    for inp, expected in vectors:
        out = run_prog(prog, inp)
        require(out == expected, f"rot13 mismatch on {inp!r}: expected {expected!r}, got {out!r}")
    print("PASS")


def test_99_bottles():
    print("Testing 99_bottles.mal (full 99-verse execution)...", end=" ", flush=True)
    prog = CORPUS_DIR / '99_bottles.mal'
    res = subprocess.run([str(MB_REF), str(prog)], input=b'', capture_output=True, check=True, timeout=20)
    require(res.returncode == 0, 'Corpus verification failed')
    require(len(res.stdout) == 11459, f"Expected 11,459 bytes, got {len(res.stdout)}")
    require(res.stdout.startswith(b"99 bottles of beer on the wall,\n99 bottles of beer,\nTake one down, pass it around,\n"), 'Corpus verification failed')
    require(b"\n1 bottle of beer on the wall.\n\n1 bottle of beer on the wall,\n1 bottle of beer,\n" in res.stdout, 'Corpus verification failed')
    require(res.stdout.endswith(b"Take one down, pass it around,\nNo more bottles of beer on the wall.\n\n"), 'Corpus verification failed')
    print("PASS (11,459 bytes, 99 verses)")


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
    test_hello_world()
    test_rot13()
    test_99_bottles()
    elapsed = time.time() - t0
    print(f"=== ALL MALBOLGE.ORG CORPUS TESTS PASSED ({elapsed:.2f}s) ===")


if __name__ == '__main__':
    main()
