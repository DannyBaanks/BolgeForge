#!/usr/bin/env python3
"""tools/verify_truth_machine_full.py - Legacy prototype challenge; current artifact is rejected by Classic loading."""
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MB_REF = REPO_ROOT / 'mb_ref' if (REPO_ROOT / 'mb_ref').exists() else (REPO_ROOT / 'oracle' / 'mb_ref')
TM_MAL = REPO_ROOT / 'artifacts' / 'truth_machine.mal'

def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def verify_truth_machine():
    print(f"=== VERIFYING TRUTH MACHINE ({TM_MAL.name}) ON mb_ref ===")
    require(MB_REF.exists(), f"mb_ref not found at {MB_REF}")
    require(TM_MAL.exists(), f"truth_machine.mal not found at {TM_MAL}")

    # Test '0': Must halt cleanly and output ONLY '0'
    p0 = subprocess.run([str(MB_REF), str(TM_MAL)], input=b"0", capture_output=True, timeout=5)
    require(p0.returncode == 0, f"Expected returncode 0 on '0', got {p0.returncode}")
    require(p0.stdout == b"0", f"Expected b'0', got {p0.stdout!r}")
    print("  [PASS] Input '0': Cleanly halts with returncode 0 and emits b'0'.")

    # A finite prefix test cannot prove infinite output or a repeated VM state.
    p1 = subprocess.run([str(MB_REF), str(TM_MAL), "20000"], input=b"1", capture_output=True, timeout=5)
    require(p1.returncode == 2, f"Expected MAX_STEPS exit 2 on '1', got {p1.returncode}")
    require(len(p1.stdout) > 1000, f"Expected continuous stream of '1's, got {len(p1.stdout)} bytes")
    require(set(p1.stdout) == {ord('1')}, f"Expected ONLY '1's, got {set(p1.stdout)}")
    print(f"  [PASS] Input '1': Finite budget produced only '1's ({len(p1.stdout)} bytes verified, 100% '1').")
    print("=== BOUNDED PREFIX CHECK ONLY; INFINITE STREAM NOT_DEMONSTRATED ===")

if __name__ == '__main__':
    verify_truth_machine()
