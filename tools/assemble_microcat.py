#!/usr/bin/env python3
"""tools/assemble_microcat.py - Algebraic Primitive Verifier & Cat 4-Battery Oracle Harness.

1. Verifies the 4 algebraic invariants for EOF detection and lossless trit storage
   across all 59,049 ternary values ([DEMONSTRATED - ALGEBRAIC]).
2. Runs the 4-battery I/O oracle harness (immediate EOF, single char, string echo,
   and binary payload with 0x00/0xFF) against Lutter's canonical reference cat.mal
   (wrapped at 72 cols in artifacts/microcat.mal as the baseline fixture).

NOTE (Epistemic Status): Standalone synthesis of a sub-1KB terminating Micro-Cat
program in self-modifying Malbolge remains [NOT_DEMONSTRATED].
"""

import sys
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MB_REF = REPO_ROOT / 'mb_ref' if (REPO_ROOT / 'mb_ref').exists() else (REPO_ROOT / 'oracle' / 'mb_ref')
ARTIFACTS_DIR = REPO_ROOT / 'artifacts'
ARTIFACTS_DIR.mkdir(exist_ok=True)
MICROCAT_OUT = ARTIFACTS_DIR / 'microcat.mal'

XLAT1 = "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha"
XLAT2 = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"

def crazy_op(x, y):
    i = 0
    p9 = [1, 9, 81, 729, 6561]
    o = [
        [4, 3, 3, 1, 0, 0, 1, 0, 0],
        [4, 3, 5, 1, 0, 2, 1, 0, 2],
        [5, 5, 4, 2, 2, 1, 2, 2, 1],
        [4, 3, 3, 1, 0, 0, 7, 6, 6],
        [4, 3, 5, 1, 0, 2, 7, 6, 8],
        [5, 5, 4, 2, 2, 1, 8, 8, 7],
        [7, 6, 6, 7, 6, 6, 4, 3, 3],
        [7, 6, 8, 7, 6, 8, 4, 3, 5],
        [8, 8, 7, 8, 8, 7, 5, 5, 4],
    ]
    for j in range(5):
        i += o[(y // p9[j]) % 9][(x // p9[j]) % 9] * p9[j]
    return i

def rot_op(x):
    return (x // 3) + (x % 3) * 19683

def make_char(target_op, c):
    idx = XLAT1.index(target_op)
    return ((idx - (c % 94)) % 94) + 33

def format_mal(byte_list, cols=72):
    lines = [byte_list[i:i + cols] for i in range(0, len(byte_list), cols)]
    return b'\n'.join(bytes(l) for l in lines) + b'\n'

def verify_artifact(path, max_steps=200000):
    print(f"Verifying {path.name} against {MB_REF.name}...")
    # Battery 1: immediate EOF (empty input)
    p1 = subprocess.run([str(MB_REF), str(path), str(max_steps)], input=b"", capture_output=True, timeout=2)
    assert p1.returncode == 0, f"Expected clean exit 0 on immediate EOF, got {p1.returncode}"
    assert p1.stdout == b"", f"Expected empty output on EOF, got {p1.stdout!r}"
    print("  [PASS] Battery 1: immediate EOF -> clean HALT (exit 0, 0 bytes out).")

    # Battery 2: single char
    p2 = subprocess.run([str(MB_REF), str(path), str(max_steps)], input=b"A", capture_output=True, timeout=2)
    assert p2.returncode == 0, f"Expected clean exit 0 on single char, got {p2.returncode}"
    assert p2.stdout == b"A", f"Expected 'A', got {p2.stdout!r}"
    print("  [PASS] Battery 2: single char 'A' -> echoed bit-for-bit, clean HALT.")

    # Battery 3: string echo with newline
    test_str = b"BolgeForge 2026 MicroCat\n"
    p3 = subprocess.run([str(MB_REF), str(path), str(max_steps)], input=test_str, capture_output=True, timeout=2)
    assert p3.returncode == 0, f"Expected clean exit 0 on string, got {p3.returncode}"
    assert p3.stdout == test_str, f"Mismatch on string echo: got {p3.stdout!r}"
    print(f"  [PASS] Battery 3: '{test_str.decode().strip()}' ({len(test_str)} B) -> exact echo bit-for-bit.")

    # Battery 4: binary payload (null byte, 0xFF, newlines)
    binary_payload = bytes([0x00, 0x41, 0xFF, 0x0A, 0x20, 0x7E])
    p4 = subprocess.run([str(MB_REF), str(path), str(max_steps)], input=binary_payload, capture_output=True, timeout=2)
    assert p4.returncode == 0, f"Expected exit 0 on binary payload, got {p4.returncode}"
    assert p4.stdout == binary_payload, f"Mismatch on binary: got {p4.stdout!r}"
    print(f"  [PASS] Battery 4: binary payload ({len(binary_payload)} B with 0x00, 0xFF) -> exact match.")
    print("=" * 60)
    print(f"ALL BATTERIES PASSED BIT-FOR-BIT FOR {path.name}!")
    print("=" * 60)

def main():
    print("=== BOLGEFORGE ALGEBRAIC PRIMITIVE & CAT ORACLE HARNESS ===", flush=True)
    if not MB_REF.exists():
        subprocess.run(["make", "mb_ref"], cwd=REPO_ROOT, check=True)

    # Formal mathematical verification of the 2-step detector and involution
    print("Checking algebraic invariants ([DEMONSTRATED - ALGEBRAIC])...")
    # Invariant 1: 2-step EOF detector -> 0 on EOF, non-zero on all 256 bytes
    assert crazy_op(crazy_op(59048, 59048), 29524) == 0
    assert all(crazy_op(crazy_op(59048, ch), 29524) != 0 for ch in range(256))
    print("  [PASS] Invariant 1: crazy(crazy(59048, EOF), 29524) == 0 (0 collisions in 256 bytes).")

    # Invariant 2: 29524 trit transposition involution across all 59,049 values
    assert all(crazy_op(crazy_op(x, 29524), 29524) == x for x in range(59049))
    print("  [PASS] Invariant 2: crazy(crazy(x, 29524), 29524) == x for all 59,049 values.")

    # Invariant 3: Universal 256-byte separator (K1=59048, K2=729)
    assert crazy_op(crazy_op(59048, 59048), 729) == 0
    assert all(crazy_op(crazy_op(ch, 59048), 729) == 1458 for ch in range(256))
    print("  [PASS] Invariant 3: Separation theorem (K1=59048, K2=729 -> EOF=0, all 256 ASCII/bytes=1458).")

    # Invariant 4: Trit-4 Target Invariant (< 188 layout)
    assert crazy_op(crazy_op(59048, 59048), 162) == 162
    assert set(crazy_op(crazy_op(x, 59048), 162) for x in range(128)) == {81}
    print("  [PASS] Invariant 4: Trit-4 invariant (< 188 layout target 162 vs 81).")

    # Baseline canonical Cat fixture (Lutter 2012, 72-column wrapped)
    cat_ref = REPO_ROOT / 'reference' / 'malbolge_org' / 'cat.mal'
    assert cat_ref.exists(), f"Missing reference {cat_ref}"
    raw_cat = cat_ref.read_bytes()
    clean_cat = [b for b in raw_cat if 33 <= b <= 126]
    formatted = format_mal(clean_cat)
    MICROCAT_OUT.write_bytes(formatted)
    print(f"Prepared baseline fixture (72-col wrapped Lutter cat.mal): {MICROCAT_OUT} ({len(formatted):,} B, {len(clean_cat):,} opcodes).")
    print("Note: Standalone sub-1KB Micro-Cat synthesis remains [NOT_DEMONSTRATED].")

    # Execute 4-battery verification
    verify_artifact(MICROCAT_OUT, max_steps=1000000)

if __name__ == '__main__':
    main()
