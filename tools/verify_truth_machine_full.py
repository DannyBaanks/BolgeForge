#!/usr/bin/env python3
"""tools/verify_truth_machine_full.py - Verify Truth Machine on mb_ref."""
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MB_REF = REPO_ROOT / 'mb_ref' if (REPO_ROOT / 'mb_ref').exists() else (REPO_ROOT / 'oracle' / 'mb_ref')
TM_MAL = REPO_ROOT / 'artifacts' / 'truth_machine.mal'

def verify_truth_machine():
    print(f"=== VERIFYING TRUTH MACHINE ({TM_MAL.name}) ON mb_ref ===")
    assert MB_REF.exists(), f"mb_ref not found at {MB_REF}"
    assert TM_MAL.exists(), f"truth_machine.mal not found at {TM_MAL}"

    # Test '0': Must halt cleanly and output ONLY '0'
    p0 = subprocess.run([str(MB_REF), str(TM_MAL)], input=b"0", capture_output=True, timeout=5)
    assert p0.returncode == 0, f"Expected returncode 0 on '0', got {p0.returncode}"
    assert p0.stdout == b"0", f"Expected b'0', got {p0.stdout!r}"
    print("  [PASS] Input '0': Cleanly halts with returncode 0 and emits b'0'.")

    # Test '1': Must loop and stream '1's indefinitely
    p1 = subprocess.run([str(MB_REF), str(TM_MAL), "20000"], input=b"1", capture_output=True, timeout=5)
    assert p1.returncode == 0, f"Expected returncode 0 on '1' max_steps, got {p1.returncode}"
    assert len(p1.stdout) > 1000, f"Expected continuous stream of '1's, got {len(p1.stdout)} bytes"
    assert set(p1.stdout) == {ord('1')}, f"Expected ONLY '1's, got {set(p1.stdout)}"
    print(f"  [PASS] Input '1': Infinitely streams '1's ({len(p1.stdout)} bytes verified, 100% '1').")
    print("=== TRUTH MACHINE 100% VERIFIED ON mb_ref ===")

if __name__ == '__main__':
    verify_truth_machine()
