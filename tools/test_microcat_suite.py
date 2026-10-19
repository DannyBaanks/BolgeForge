#!/usr/bin/env python3
"""tools/test_microcat_suite.py - Verification suite for microcat.mal on mb_ref."""
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MB_REF = (REPO_ROOT / 'mb_ref') if (REPO_ROOT / 'mb_ref').exists() else (REPO_ROOT / 'oracle' / 'mb_ref')
MAL_FILE = REPO_ROOT / 'artifacts' / 'microcat.mal'

assert MB_REF.exists(), f"mb_ref not found at {MB_REF}"
assert MAL_FILE.exists(), f"microcat.mal not found at {MAL_FILE}"

print(f"=== MICROCAT 3,380B TEST SUITE ON mb_ref ===")
print(f"Target: {MAL_FILE} ({MAL_FILE.stat().st_size} bytes)")

# Battery 1: Empty input
p = subprocess.run([str(MB_REF), str(MAL_FILE)], input=b'', capture_output=True)
assert p.returncode == 0, f"Battery 1 failed rc: {p.returncode}"
assert p.stdout == b'', f"Battery 1 failed stdout: {p.stdout!r}"
print("  [PASS] BATTERY 1: Immediate EOF halts with rc=0 and 0 bytes emitted.")

# Battery 2: All 256 bytes individually
print("  [RUN ] Testing all 256 byte values (0x00..0xFF)...")
failed = []
for b in range(256):
    in_b = bytes([b])
    p = subprocess.run([str(MB_REF), str(MAL_FILE)], input=in_b, capture_output=True)
    if p.returncode != 0 or p.stdout != in_b:
        failed.append((b, p.returncode, p.stdout))

if not failed:
    print("  [PASS] BATTERY 2: All 256/256 bytes echo with 100% bit-for-bit fidelity and clean exit 0!")
else:
    print(f"  [FAIL] Failed on {len(failed)} bytes: {failed[:5]}")
    sys.exit(1)

# Battery 2+: Two-byte corner cases
two_byte_samples = [
    b'AB', b'hi', b'12', b'\n\n', b'\x00\x00', b'\xff\xff',
    bytes([0, 255]), bytes([255, 0]), bytes([127, 128]), bytes([65, 0]), bytes([0, 65])
]
for payload in two_byte_samples:
    p = subprocess.run([str(MB_REF), str(MAL_FILE)], input=payload, capture_output=True)
    assert p.returncode == 0 and p.stdout == payload, f"Battery 2+ failed on {payload!r}: {p}"
print("  [PASS] BATTERY 2+: Two-byte corner cases echo bit-for-bit with clean exit 0.")

# Battery 3: Three-byte corner cases & binary permutations
three_byte_samples = [
    b'ABC', b'xyz', b'123', b'Foo', b'Bar', b'cat', b'\r\n\x00',
    bytes([0, 0, 0]), bytes([255, 255, 255]), bytes([0, 128, 255]),
    bytes([255, 128, 0]), bytes([0, 255, 0]), bytes([255, 0, 255]),
    bytes([1, 2, 3]), bytes([254, 255, 0]), bytes([0, 1, 0])
]
for payload in three_byte_samples:
    p = subprocess.run([str(MB_REF), str(MAL_FILE)], input=payload, capture_output=True)
    assert p.returncode == 0 and p.stdout == payload, f"Battery 3 failed on {payload!r}: {p}"
print("  [PASS] BATTERY 3: Three-byte corner cases & binary permutations echo bit-for-bit.")

print("\n>>> ALL VERIFIED ON OLMSTEAD REFERENCE INTERPRETER (mb_ref)!")
