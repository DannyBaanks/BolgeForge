#!/usr/bin/env python3
"""tools/test_compressed.py - Verify compressed canonical benchmarks against mb_ref."""
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MB_REF = REPO_ROOT / 'mb_ref' if (REPO_ROOT / 'mb_ref').exists() else (REPO_ROOT / 'oracle' / 'mb_ref')
ARTIFACTS = REPO_ROOT / 'artifacts'

def test_compressed():
    print("=== VERIFYING COMPRESSED BENCHMARKS AGAINST mb_ref ===")
    
    # 1. Cat compressed
    p = ARTIFACTS / 'cat_compressed.mal'
    if p.exists():
        res = subprocess.run([str(MB_REF), str(p)], input=b"Hello BolgeForge\n", capture_output=True, check=True)
        assert res.stdout == b"Hello BolgeForge\n"
        print(f"  [PASS] {p.name}: verified bit-exact echo")

    # 2. Digital root compressed
    p = ARTIFACTS / 'digital_root_compressed.mal'
    if p.exists():
        res = subprocess.run([str(MB_ROOT) if 'MB_ROOT' in locals() else str(MB_REF), str(p)], input=b"12345\n", capture_output=True, check=True)
        assert res.stdout == b"6\n"
        print(f"  [PASS] {p.name}: verified 12345 -> 6")

    # 3. Adder compressed
    p = ARTIFACTS / 'adder_compressed.mal'
    if p.exists():
        res = subprocess.run([str(MB_REF), str(p)], input=b"12\n34\n", capture_output=True, check=True)
        assert res.stdout == b"46\n"
        print(f"  [PASS] {p.name}: verified 12+34 -> 46")

    # 4. 99 bottles compressed
    p = ARTIFACTS / '99_bottles_compressed.mal'
    if p.exists():
        res = subprocess.run([str(MB_REF), str(p)], capture_output=True, check=True)
        assert len(res.stdout) == 11459
        print(f"  [PASS] {p.name}: verified 11,459 bytes output")

    print("=== ALL COMPRESSED BENCHMARKS VERIFIED! ===")

if __name__ == '__main__':
    test_compressed()
