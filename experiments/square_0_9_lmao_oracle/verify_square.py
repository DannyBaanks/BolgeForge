#!/usr/bin/env python3
"""Verify the LMAO-derived square(0..9) oracle experiment."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MB_REF = ROOT / "mb_ref"
ARTIFACT = HERE / "square.mal"
SOURCE = HERE / "square.hell"
EXPECTED_SHA256 = {
    "square.mal": "391b9641691f310170ecb64daefd61fce2621adc640dba10e3149e4f286bae26",
    "square.hell": "70edc01d64413e837fb431ef2cf87cf9599c00ba94eb101f5f67248f8970dd07",
}
EXPECTED = {digit: f"{digit * digit}\n".encode() for digit in range(10)}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_one(payload: bytes) -> tuple[int, bytes, bytes]:
    result = subprocess.run(
        [str(MB_REF), str(ARTIFACT)],
        input=payload,
        capture_output=True,
        timeout=30,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from tools.prove_truth_machine import loader_cells

    checks: dict[str, bool] = {}
    details: dict[str, object] = {}

    for name, expected in EXPECTED_SHA256.items():
        actual = sha256(HERE / name)
        checks[f"{name}_sha256"] = actual == expected
        details[f"{name}_sha256"] = actual

    try:
        cells = loader_cells(ARTIFACT.read_bytes())
        checks["strict_loader_accept"] = len(cells) == 59049
        details["loader_cells"] = len(cells)
    except ValueError as error:
        checks["strict_loader_accept"] = False
        details["loader_error"] = str(error)

    vectors = []
    for digit, expected in EXPECTED.items():
        for suffix in (b"", b"\n"):
            payload = bytes([48 + digit]) + suffix
            returncode, stdout, stderr = run_one(payload)
            ok = returncode == 0 and stdout == expected and stderr == b""
            vectors.append(
                {
                    "input_hex": payload.hex(),
                    "returncode": returncode,
                    "stdout_hex": stdout.hex(),
                    "stderr_hex": stderr.hex(),
                    "ok": ok,
                }
            )
            checks[f"vector_{payload.hex()}"] = ok
    details["vectors"] = vectors

    if not MB_REF.exists():
        print(f"missing oracle: {MB_REF}; run `make mb_ref`", file=sys.stderr)
        return 1

    verdict = "DEMONSTRATED" if all(checks.values()) else "NOT_DEMONSTRATED"
    report = {
        "experiment": "square_0_9_lmao_oracle",
        "artifact": str(ARTIFACT.relative_to(ROOT)),
        "source": str(SOURCE.relative_to(ROOT)),
        "provenance": "LMAO v0.6.0 / GPL-3 derived; oracle experiment, not BolgeForge synthesis",
        "checks": checks,
        "details": details,
        "verdict": verdict,
    }
    print(json.dumps(report, indent=2))
    return 0 if verdict == "DEMONSTRATED" else 1


if __name__ == "__main__":
    sys.exit(main())
