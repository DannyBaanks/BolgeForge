#!/usr/bin/env python3
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from constants import CHAR_OP_MAP, XLAT1, char_for_op, crazy_op, rot_op

VALID = frozenset("ji*p</vo")


def decode(addr: int, value: int):
    if not 33 <= value <= 126:
        return None
    return XLAT1[(value - 33 + addr) % 94]


def valid_cell(addr: int, value: int) -> bool:
    return 33 <= value <= 126 and decode(addr, value) in VALID


_VALID_VALUES = {}


def valid_values(addr: int):
    if addr not in _VALID_VALUES:
        _VALID_VALUES[addr] = [v for v in range(33, 127) if valid_cell(addr, v)]
    return _VALID_VALUES[addr]


def best_ops(data_addr: int, a: int, target: int, max_len: int = 6, limit: int = 8):
    states = {(0, a): ((), ())}
    found = []
    for pos in range(max_len + 1):
        for (p, current), (ops, data) in list(states.items()):
            if p == pos and (current & 255) == target:
                found.append((ops, data))
        if pos == max_len:
            break
        new_states = {}
        for (p, current), (ops, data) in states.items():
            if p != pos:
                continue
            for value in valid_values(data_addr + pos):
                for opcode, result in (("*", rot_op(value)), ("p", crazy_op(current, value))):
                    key = (pos + 1, result)
                    if key not in new_states:
                        new_states[key] = (ops + (opcode,), data + (value,))
        states.update(new_states)
    found.sort(key=lambda item: len(item[0]))
    return found[:limit]


def constants():
    c = 85
    rotations = 7
    s = [crazy_op(48 + digit, c) for digit in range(10)]
    for _ in range(rotations):
        s = [rot_op(value) for value in s]
    q = [crazy_op(value, 48) for value in s]
    return s, q


def recipe_options(digit: int, q_value: int, target: bytes, max_k: int = 6):
    options = []
    for k in range(1, max_k + 1):
        b = q_value
        for _ in range(k):
            b = rot_op(b)
        b += 1
        setup_len = 3 * k + 3
        max_code = 26 - setup_len
        if max_code < 3:
            continue
        solutions = []

        def walk(index, a, data_addr, groups, data_values):
            if len(solutions) >= 8:
                return
            if index == len(target):
                code = "".join("".join(group) + "<" for group in groups) + "v"
                if len(code) <= max_code:
                    solutions.append((code, tuple(data_values), b, len(code)))
                return
            for ops, data in best_ops(data_addr, a, target[index], min(6, max_code), 6):
                next_a = a
                for opcode, value in zip(ops, data):
                    next_a = rot_op(value) if opcode == "*" else crazy_op(next_a, value)
                walk(index + 1, next_a, data_addr + len(ops) + 1, groups + (ops,), data_values + data)
                if len(solutions) >= 8:
                    return

        walk(0, b - 1, b, (), ())
        for code, data, b_value, length in solutions:
            options.append(
                {
                    "k": k,
                    "b": b_value,
                    "setup": setup_len,
                    "length": length,
                    "code": code,
                    "data": data,
                    "cells": tuple(range(b_value, b_value + length)),
                }
            )
    seen = set()
    unique = []
    for option in options:
        key = (option["k"], option["b"], option["code"], option["data"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(option)
    unique.sort(key=lambda option: (option["k"], option["length"], len(option["data"])))
    return unique


def select_options(s_values, q_values, targets):
    all_options = {}
    for digit in range(10):
        all_options[digit] = recipe_options(digit, q_values[digit], targets[digit])
    used = set(range(0, 22))
    used.update((40, 49, 50, 51, 78, 84, 85))
    for digit in range(10):
        used.update(range(s_values[digit] + 1, s_values[digit] + 5))
        used.update(range(q_values[digit] + 1, q_values[digit] + 27))
    for digit in range(10):
        all_options[digit] = [
            option for option in all_options[digit] if not (set(option["cells"]) & used)
        ]
    order = sorted(range(10), key=lambda digit: (len(all_options[digit]), digit))
    selected = {}
    occupied = set(used)

    def backtrack(index):
        if index == len(order):
            return True
        digit = order[index]
        for option in all_options[digit]:
            cells = set(option["cells"])
            if cells & occupied:
                continue
            selected[digit] = option
            occupied.update(cells)
            if backtrack(index + 1):
                return True
            occupied.difference_update(cells)
            del selected[digit]
        return False

    if not backtrack(0):
        raise RuntimeError("no disjoint recipe selection")
    return selected


def build(s_values, q_values, selected):
    size = max(
        max(s_values) + 5,
        max(q_values) + 27,
        max(option["b"] + option["length"] for option in selected.values()),
        90,
    ) + 2
    memory = [ord(char_for_op(CHAR_OP_MAP["j"], addr)) for addr in range(size)]
    bootstrap = ["/", "j", "j", "j", "j", "p"] + ["j", "*"] * 7 + ["j", "i"]
    for addr, opcode in enumerate(bootstrap):
        memory[addr] = ord(char_for_op(CHAR_OP_MAP[opcode], addr))
    for addr, value in {40: 77, 49: 85, 50: 48, 51: 83, 78: 84, 84: 49, 85: 48}.items():
        memory[addr] = value
    for digit in range(10):
        addr = s_values[digit] + 1
        for offset, opcode in enumerate("pjj i".replace(" ", "")):
            memory[addr + offset] = ord(char_for_op(CHAR_OP_MAP[opcode], addr + offset))
        option = selected[digit]
        setup = "".join(["jj*"] * option["k"]) + "jjj"
        addr = q_values[digit] + 1
        for offset, opcode in enumerate(setup):
            memory[addr + offset] = ord(char_for_op(CHAR_OP_MAP[opcode], addr + offset))
        addr = q_values[digit] + 1 + len(setup)
        for offset, opcode in enumerate(option["code"]):
            memory[addr + offset] = ord(char_for_op(CHAR_OP_MAP[opcode], addr + offset))
        data_addr = option["b"]
        data_index = 0
        for group in option["code"].split("<"):
            for opcode in group.replace("v", ""):
                memory[data_addr] = option["data"][data_index]
                data_index += 1
                data_addr += 1
            data_addr += 1
        if data_index != len(option["data"]):
            raise AssertionError("recipe data length mismatch")
    for addr, value in enumerate(memory):
        if not valid_cell(addr, value):
            raise AssertionError(f"invalid cell {addr}: {value}")
    return bytes(memory)


def verify(path: Path, expected):
    oracle = ROOT / "oracle" / "mb_ref"
    if not oracle.exists():
        raise RuntimeError(f"missing oracle: {oracle}")
    for digit in range(10):
        result = subprocess.run(
            [str(oracle), str(path)],
            input=str(digit),
            text=True,
            capture_output=True,
            timeout=20,
        )
        if result.returncode != 0 or result.stdout != expected[digit]:
            raise AssertionError(
                f"mb_ref failed for {digit}: rc={result.returncode} "
                f"stdout={result.stdout!r} stderr={result.stderr!r}"
            )
    from tools.prove_truth_machine import loader_cells, run

    memory = loader_cells(path.read_bytes())
    for digit in range(10):
        result = run(memory, str(digit).encode(), 200000)
        if result["status"] != "HALT" or result["output"] != expected[digit].encode():
            raise AssertionError(f"strict loader failed for {digit}: {result}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("native_square.mal"))
    args = parser.parse_args()
    s_values, q_values = constants()
    expected = [f"{digit * digit}\n" for digit in range(10)]
    selected = select_options(s_values, q_values, [value.encode() for value in expected])
    source = build(s_values, q_values, selected)
    args.out.write_bytes(source)
    verify(args.out, expected)
    print("selected")
    for digit in range(10):
        option = selected[digit]
        print(
            f"{digit}: k={option['k']} B={option['b']} "
            f"setup={option['setup']} L={option['length']} "
            f"code={option['code']} data={option['data']}"
        )
    print(f"bytes={len(source)} sha256={hashlib.sha256(source).hexdigest()}")


if __name__ == "__main__":
    main()
