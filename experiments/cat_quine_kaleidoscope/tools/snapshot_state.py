#!/usr/bin/env python3
"""snapshot_state.py - run the Python Malbolge sim of the m=281 candidate to
step N and dump the machine state (registers + memory zones) as JSON.

Usage: snapshot_state.py <prog.mal> <steps> [out.json]

Load/step semantics must match oracle/mb_ref.c exactly.
"""
import json
import sys

sys.setrecursionlimit(10000)

XLAT1 = "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha"
XLAT2 = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"

_CRAZY = ((1, 0, 0), (1, 0, 2), (2, 2, 1))


def crazy_op(x, y):
    res = 0
    p = 1
    for _ in range(10):
        res += _CRAZY[y % 3][x % 3] * p
        x //= 3
        y //= 3
        p *= 3
    return res


def rot_op(x):
    return (x // 3) + (x % 3) * 19683


def load(path):
    mem = []
    with open(path, "rb") as f:
        data = f.read()
    for b in data:
        ch = chr(b)
        if ch.isspace():
            continue
        if 33 <= b <= 126:
            mem.append(b)
        else:
            mem.append(crazy_op(mem[-1], mem[-2]))
    while len(mem) < 59049:
        mem.append(crazy_op(mem[-1], mem[-2]))
    return mem


def main():
    prog, steps = sys.argv[1], int(sys.argv[2])
    out = sys.argv[3] if len(sys.argv) > 3 else None
    mem = load(prog)
    c = d = a = 0
    step = 0
    while step < steps:
        v = mem[c]
        op = XLAT1[(v - 33 + c) % 94]
        if op == "j":
            d = mem[d]
        elif op == "i":
            c = mem[d]
        elif op == "*":
            a = mem[d] = rot_op(mem[d])
        elif op == "p":
            a = mem[d] = crazy_op(a, mem[d])
        elif op == "<":
            pass
        elif op == "/":
            a = 59048  # stdin exhausted
        elif op == "v":
            step += 1
            break
        if 33 <= mem[c] <= 126:
            mem[c] = ord(XLAT2[mem[c] - 33])
        c = 0 if c == 59048 else c + 1
        d = 0 if d == 59048 else d + 1
        step += 1
    state = {
        "prog": prog, "steps": step, "c": c, "d": d, "a": a,
        "mem_snapshot": {str(i): mem[i] for i in range(len(mem))},
    }
    if out:
        with open(out, "w") as f:
            json.dump(state, f)
        print(f"wrote {out}: steps={step} c={c} d={d} a={a}")
    else:
        zones = [(0, 180), (25550, 25580), (26160, 26420), (29360, 29390),
                 (29470, 29495), (52820, 52840), (59040, 59049)]
        for lo, hi in zones:
            print(f"--- [{lo}..{hi}] ---")
            for i in range(lo, hi):
                print(f"{i:6d} {mem[i]:6d}")
    # scans
    print("--- scan: cells == 26407 / 26408 / 25975 / 25947 / 29479 / 29371 ---")
    targets = {26407, 26408, 25975, 25947, 29479, 29371, 154, 153, 155}
    for i, v in enumerate(mem):
        if v in targets:
            print(f"cell {i} = {v}")
    print("--- scan: big values (>=20000) below 26414 ---")
    for i in range(26414):
        if mem[i] >= 20000:
            print(f"cell {i} = {mem[i]}")


if __name__ == "__main__":
    main()
