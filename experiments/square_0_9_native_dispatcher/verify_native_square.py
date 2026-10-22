#!/usr/bin/env python3
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.prove_truth_machine import loader_cells, run

ARTIFACT = Path(__file__).with_name("native_square.mal")
EXPECTED_SHA256 = "6026ddc03133c824d821dcc5b779fce414fd07c2e3d3c8591b8bcaadcbcfd6d0"
EXPECTED = [f"{digit * digit}\n" for digit in range(10)]


def main():
    source = ARTIFACT.read_bytes()
    actual = hashlib.sha256(source).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"artifact hash mismatch: {actual}")
    memory = loader_cells(source)
    oracle = ROOT / "oracle" / "mb_ref"
    for digit in range(10):
        result = subprocess.run(
            [str(oracle), str(ARTIFACT)],
            input=str(digit),
            text=True,
            capture_output=True,
            timeout=20,
        )
        if result.returncode != 0 or result.stdout != EXPECTED[digit]:
            raise SystemExit(
                f"mb_ref failed for {digit}: rc={result.returncode} "
                f"stdout={result.stdout!r} stderr={result.stderr!r}"
            )
        strict = run(memory, str(digit).encode(), 200000)
        if strict["status"] != "HALT" or strict["output"] != EXPECTED[digit].encode():
            raise SystemExit(f"strict loader failed for {digit}: {strict}")
        print(f"{digit}: {EXPECTED[digit]!r} HALT")
    print(f"artifact={ARTIFACT.name} bytes={len(source)} sha256={actual}")
    print(f"cells={len(memory)} builder=build_native_square.py")


if __name__ == "__main__":
    main()
