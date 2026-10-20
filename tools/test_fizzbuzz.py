#!/usr/bin/env python3
"""tools/test_fizzbuzz.py - Verification suite for FizzBuzz in Classic Malbolge.

Validates artifacts/fizzbuzz.mal against the Olmstead reference oracle (mb_ref):
1. Verifies exact SHA-256 and ASCII loader invariants (bytes 33..126).
2. Executes artifacts/fizzbuzz.mal on mb_ref.
3. Asserts clean exit code 0, empty stderr, and bit-exact 413-byte output matching
   the canonical 100-line FizzBuzz specification.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MB_REF = REPO_ROOT / "mb_ref" if (REPO_ROOT / "mb_ref").exists() else (REPO_ROOT / "oracle" / "mb_ref")
FIZZBUZZ_MAL = REPO_ROOT / "artifacts" / "fizzbuzz.mal"
EXPECTED_SHA256 = "14f372ac74909c344638bf5c1ffbf1797fcd9b26cb18111a3b21bc31dd1bcd42"


def generate_expected_fizzbuzz() -> bytes:
    lines = []
    for i in range(1, 101):
        if i % 15 == 0:
            lines.append("FizzBuzz\n")
        elif i % 3 == 0:
            lines.append("Fizz\n")
        elif i % 5 == 0:
            lines.append("Buzz\n")
        else:
            lines.append(f"{i}\n")
    return "".join(lines).encode("latin1")


def main() -> int:
    print("=== VERIFYING FIZZBUZZ (1..100) IN CLASSIC MALBOLGE ===")
    if not FIZZBUZZ_MAL.exists():
        print(f"FAIL: {FIZZBUZZ_MAL} does not exist.")
        return 1

    content = FIZZBUZZ_MAL.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    print(f"Artifact: {FIZZBUZZ_MAL}")
    print(f"Size:     {len(content):,} bytes (wrapped)")
    print(f"SHA-256:  {digest}")

    if digest != EXPECTED_SHA256:
        print(f"FAIL: SHA-256 mismatch! Expected {EXPECTED_SHA256}, got {digest}")
        return 1
    print("  [PASS] Artifact hash matches canonical recorded checksum.")

    # ASCII Invariant check:
    opcodes = [b for b in content if b not in (ord("\n"), ord("\r"), ord(" "), ord("\t"))]
    print(f"Opcodes:  {len(opcodes):,} non-whitespace bytes")
    for idx, b in enumerate(opcodes):
        if not (33 <= b <= 126):
            print(f"FAIL: Byte at opcode {idx} is outside ASCII [33, 126]: {b}")
            return 1
    print("  [PASS] All opcodes strictly satisfy ASCII [33, 126] loader constraint.")

    if not MB_REF.exists():
        print(f"Building oracle: {MB_REF}...")
        subprocess.run(["gcc", "-O2", "-o", str(REPO_ROOT / "mb_ref"), str(REPO_ROOT / "oracle" / "mb_ref.c")], check=True)

    expected_output = generate_expected_fizzbuzz()
    assert len(expected_output) == 413, f"Spec size error: {len(expected_output)}"

    t0 = time.perf_counter()
    res = subprocess.run([str(MB_REF), str(FIZZBUZZ_MAL)], capture_output=True, timeout=10)
    dt = time.perf_counter() - t0

    if res.returncode != 0:
        print(f"FAIL: Program exited with returncode {res.returncode}")
        return 1
    print(f"  [PASS] Clean HALT (rc=0) executed in {dt*1000:.2f} ms.")

    if res.stderr:
        print(f"FAIL: Unexpected stderr output: {res.stderr!r}")
        return 1

    if res.stdout != expected_output:
        print(f"FAIL: Output mismatch! Emitted {len(res.stdout)} bytes vs expected {len(expected_output)} bytes.")
        print("First 200 bytes received:")
        print(res.stdout[:200].decode("latin1", errors="replace"))
        return 1

    lines = res.stdout.decode("latin1").splitlines(keepends=True)
    if len(lines) != 100:
        print(f"FAIL: Expected 100 lines, got {len(lines)}")
        return 1

    # Check key milestone lines
    assert lines[0] == "1\n", f"Line 1 failed: {lines[0]}"
    assert lines[1] == "2\n", f"Line 2 failed: {lines[1]}"
    assert lines[2] == "Fizz\n", f"Line 3 failed: {lines[2]}"
    assert lines[4] == "Buzz\n", f"Line 5 failed: {lines[4]}"
    assert lines[14] == "FizzBuzz\n", f"Line 15 failed: {lines[14]}"
    assert lines[29] == "FizzBuzz\n", f"Line 30 failed: {lines[29]}"
    assert lines[89] == "FizzBuzz\n", f"Line 90 failed: {lines[89]}"
    assert lines[97] == "98\n", f"Line 98 failed: {lines[97]}"
    assert lines[98] == "Fizz\n", f"Line 99 failed: {lines[98]}"
    assert lines[99] == "Buzz\n", f"Line 100 failed: {lines[99]}"

    print(f"  [PASS] Exact 100 lines, 413 bytes emitted bit-for-bit identical to canonical spec.")
    print("======================================================================")
    print("SUCCESS: FIZZBUZZ IN CLASSIC MALBOLGE FULLY VERIFIED ON mb_ref!")
    print("======================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
