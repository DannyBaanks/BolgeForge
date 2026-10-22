#!/usr/bin/env python3
"""Reproduce the address-packing blocker for a native product(0..9)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from constants import CHAR_OP_MAP, XLAT1, XLAT2, char_for_op, crazy_op, rot_op

S = [28471, 28444, 28498, 28633, 28606, 28660, 28795, 28768, 28822, 28714]
TRANSFORMS = [
    (1, 95, 6),
    (1, 98, 7),
    (3, 121, 4),
    (1, 125, 5),
    (2, 122, 7),
    (3, 67, 6),
    (0, 53, 6),
    (3, 67, 5),
    (3, 64, 7),
    (3, 67, 4),
]


def rotn(value, count):
    for _ in range(count):
        value = rot_op(value)
    return value


def packing_addresses():
    return [
        rotn(crazy_op(rotn(s, r1), c), r2)
        for r1, c, r2 in TRANSFORMS
        for s in S
    ]


def stats(values):
    ordered = sorted(values)
    return {
        "count": len(values),
        "unique": len(set(values)),
        "min": min(values),
        "max": max(values),
        "min_gap": min(b - a for a, b in zip(ordered, ordered[1:])),
    }


def bootstrap_reaches(c50):
    size = 60000
    memory = [ord(char_for_op(CHAR_OP_MAP["j"], addr)) for addr in range(size)]
    for addr, value in {40: 77, 49: 85, 50: c50, 51: 83, 78: 84, 84: 49, 85: 48}.items():
        memory[addr] = value
    base = 1000
    bootstrap = ["/", "j", "j", "j", "j", "p"] + ["j", "*"] * 7 + ["j", "i"]
    for offset, opcode in enumerate(bootstrap):
        memory[base + offset] = ord(char_for_op(CHAR_OP_MAP[opcode], base + offset))
    for s in S:
        addr = s + 1
        for offset, opcode in enumerate("pjj i".replace(" ", "")):
            memory[addr + offset] = ord(char_for_op(CHAR_OP_MAP[opcode], addr + offset))
    a = 0
    c = base
    d = 0
    for _ in range(10000):
        try:
            if not 33 <= memory[c] <= 126:
                return False
            opcode = XLAT1[(memory[c] - 33 + c) % 94]
            if c == S[3] + 1:
                return (a, d, memory[50]) == (S[3], 50, 48)
            if opcode == "j":
                d = memory[d]
            elif opcode == "i":
                c = memory[d]
            elif opcode == "*":
                a = memory[d] = rot_op(memory[d])
            elif opcode == "p":
                a = memory[d] = crazy_op(a, memory[d])
            elif opcode == "/":
                a = 48 + 3
            elif opcode == "v":
                return False
            memory[c] = ord(XLAT2[memory[c] - 33])
            c = (c + 1) % 59049
            d = (d + 1) % 59049
        except IndexError:
            return False
    return False


def main():
    packing = packing_addresses()
    branch = [crazy_op(value, 48) for value in packing]
    working = [value for value in range(33, 127) if bootstrap_reaches(value)]
    result = {
        "transform_sets": len(TRANSFORMS),
        "packing_before_branch": stats(packing),
        "packing_after_branch": stats(branch),
        "bootstrap_c50_working": working,
        "verdict": "NOT_DEMONSTRATED",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    ok = (
        result["packing_before_branch"]["unique"] == 100
        and result["packing_before_branch"]["min_gap"] >= 27
        and (
            result["packing_after_branch"]["unique"] < 100
            or result["packing_after_branch"]["min_gap"] < 27
        )
        and working == [48]
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
