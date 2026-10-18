#!/usr/bin/env python3
"""tools/synthesize_truth_machine.py - The First BolgeForge Truth Machine in Classic Malbolge.

Specification (Standard Esolang Truth-Machine):
  - Read 1 character from standard input ('0' or '1').
  - If input is '0' (ASCII 48): Output '0' and cleanly HALT with exit code 0.
  - If input is '1' (ASCII 49): Output '1' indefinitely in an infinite loop.

Verified against mb_ref (Olmstead classic Malbolge, 59,049 cells).
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MB_REF = REPO_ROOT / "mb_ref"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)
OUT_MAL = ARTIFACTS_DIR / "truth_machine.mal"

XLAT1 = "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha"
XLAT2 = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
MEM_SIZE = 59049


def char_for_op(op_char: str, c: int) -> int:
    idx = XLAT1.index(op_char)
    return ((idx - (c % 94)) % 94) + 33


def build_truth_machine() -> bytes:
    """Builds the 103-byte deterministic Truth Machine in Classic Malbolge."""
    N = 103
    prog = [ord('o')] * N

    # 1. Two-step Ternary Discriminator into Low Memory (c=0..7):
    # Algebraic mapping: op(op(a, 33), 36) maps:
    #   a = 48 ('0') -> 36  (lands on c=37)
    #   a = 49 ('1') -> 37  (lands on c=38)
    prog[0] = char_for_op('/', 0) # in -> a = 48 or 49
    prog[1] = char_for_op('<', 1) # out -> print initial '0' or '1'
    prog[2] = char_for_op('j', 2) # d = mem[2] + 1 = 38 + 1 = 39
    prog[3] = char_for_op('p', 3) # mem[39] = op(a, mem[39])
    prog[4] = char_for_op('j', 4) # d = mem[40] + 1 = 83 + 1 = 84
    prog[5] = char_for_op('p', 5) # mem[84] = op(a, mem[84])
    prog[6] = char_for_op('j', 6) # d = mem[85] + 1 = 83 + 1 = 84
    prog[7] = char_for_op('i', 7) # c = mem[84] -> 36 or 37 (+1 = 37 or 38)

    # 2. Branch 0 (Halt Cell):
    prog[37] = char_for_op('v', 37) # clean halt for input '0'

    # 3. Data cells for Discriminator:
    prog[39] = 33 # '!' (Y=33)
    prog[40] = 83 # 'S' (target for j at c=4)
    prog[84] = 36 # '$' (Z=36)
    prog[85] = 83 # 'S' (target for j at c=6, and crazy at c=38)

    # 4. Branch 1 Handoff (c=38..42):
    # At c=38: op(37, 83) = 29489 -> loaded into a (29489 % 256 = 49 = '1')
    prog[38] = char_for_op('p', 38)
    prog[41] = ord('o')           # NOP padding for modulo 3 alignment
    prog[42] = char_for_op('i', 42) # jumps to 75 via mem[89] (d=89), lands on c=76 with d=90

    # 5. Closed Limit Cycle Loop (c=76..78):
    prog[75] = ord('o') # sacrificial encryption cell for jumps
    prog[76] = 58       # ':' (Cycle 1: j -> $ -> J -> < -> @ -> ')
    prog[77] = ord('o') # NOP
    prog[78] = 114      # 'r' (Cycle 3: 'i' jump to 75, immutable jump cell)

    # 6. Modulo 3 Disjoint Runway Data:
    # All jump target cells (congruent to 2 mod 3) contain 75
    for d in range(86, N):
        if d % 3 == 2:
            prog[d] = 75

    # Reset target cells for 'j' (congruent to 0 mod 3):
    prog[90] = 84   # handoff reset: d becomes 84 + 1 = 85
    prog[102] = 84  # periodic reset on pass 7: d becomes 84 + 1 = 85

    return bytes(prog)


def verify_with_mb_ref(mal_path: Path) -> None:
    print(f"\nVerifying {mal_path.name} against {MB_REF}...")

    # Test Input '0'
    p0 = subprocess.run(
        [str(MB_REF), str(mal_path)],
        input=b"0",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert p0.returncode == 0, f"Input '0' failed with return code {p0.returncode}!"
    assert p0.stdout == b"0", f"Input '0' expected output b'0', got {p0.stdout}!"
    print("  [PASS] Input '0': Exits with code 0, stdout = b'0'")

    # Test Input '1' (50,000 steps)
    p1 = subprocess.run(
        [str(MB_REF), str(mal_path), "50000"],
        input=b"1",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert p1.returncode == 0, f"Input '1' failed with return code {p1.returncode}!"
    assert len(p1.stdout) >= 2000, f"Input '1' expected >= 2000 chars, got {len(p1.stdout)}!"
    assert set(p1.stdout) == {ord("1")}, f"Input '1' contains non-'1' characters: {set(p1.stdout)}!"
    print(f"  [PASS] Input '1': Sustained infinite loop ({len(p1.stdout)} pure '1' chars in 50k steps)")


def main() -> None:
    print("=" * 60)
    print("BolgeForge: Truth Machine in Classic Malbolge (Olmstead 1998)")
    print("=" * 60)

    t0 = time.time()
    code = build_truth_machine()
    OUT_MAL.write_bytes(code)
    dt = (time.time() - t0) * 1000

    sha = hashlib.sha256(code).hexdigest()
    print(f"Generated: {OUT_MAL}")
    print(f"Size:      {len(code)} bytes")
    print(f"SHA-256:   {sha}")
    print(f"Build time: {dt:.2f} ms")

    verify_with_mb_ref(OUT_MAL)

    print("\n" + "=" * 60)
    print("ALL VERIFICATIONS PASSED: 100% BIT-FOR-BIT CANONICAL SUCCESS")
    print("=" * 60)


if __name__ == "__main__":
    main()
