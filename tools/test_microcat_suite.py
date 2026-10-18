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

print(f"=== MICROCAT 430B TEST SUITE ON mb_ref ===")
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

print("\n>>> ALL VERIFIED ON OLMSTEAD REFERENCE INTERPRETER (mb_ref)!")
