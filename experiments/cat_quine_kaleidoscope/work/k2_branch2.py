#!/usr/bin/env python3
"""K2: corrected final branch-write search (full y_f sweep).

After gate, a = B (payload) or A (EOF). Final write at cell d3 (holding y_f):
mem[d3] := op(a, y_f). If routing returns d to d3, i reads that value and
c++ reaches the landing. A consecutive p;i is not sufficient: p increments d.
data landing Et = op(B,y_f)+1 and EOF landing Ht = op(A,y_f)+1 must both be
Q-dead safe-zone cells, Et != Ht, y_f reachable (k2_reach_full.pkl).

Unlike k2_branch.py, sweep all reachable y_f and use the real EOF value:
59048 = 88888 in base 9, not 22222 (which is 14762).
The digit-preimage filter is only a necessary condition; exact membership of
both landing addresses is checked below. These are algebraic candidates, not
VM programs: register routing, writes and per-byte rearming remain unverified.
"""
import argparse
import pickle
from collections import defaultdict
from pathlib import Path

P9 = [1, 9, 81, 729, 6561]
O = [
    [4, 3, 3, 1, 0, 0, 1, 0, 0],
    [4, 3, 5, 1, 0, 2, 1, 0, 2],
    [5, 5, 4, 2, 2, 1, 2, 2, 1],
    [4, 3, 3, 1, 0, 0, 7, 6, 6],
    [4, 3, 5, 1, 0, 2, 7, 6, 8],
    [5, 5, 4, 2, 2, 1, 8, 8, 7],
    [7, 6, 6, 7, 6, 6, 4, 3, 3],
    [7, 6, 8, 7, 6, 8, 4, 3, 5],
    [8, 8, 7, 8, 8, 7, 5, 5, 4],
]

def digits(v):
    return [(v // P9[j]) % 9 for j in range(5)]

def from_digits(ds):
    return sum(d * p for d, p in zip(ds, P9))

def opw(x, y):
    return sum(O[(y // P9[j]) % 9][(x // P9[j]) % 9] * P9[j] for j in range(5))

SAFE_ZONE = (set(range(25647, 25947)) | set(range(25949, 25975)) |
             set(range(25977, 26004)) | {26006, 26007} |
             set(range(26010, 26098)) | {26100} | set(range(26103, 26123)) |
             {26191, 26195})


def search(depth, *, stored=False):
    """Search the supplied value/depth cache; cost excludes register routing."""
    reach = sorted(depth)
    inputs = [opw(b, 29524) if stored else b for b in range(256)]
    eof_digits = digits(opw(59048, 29524) if stored else 59048)
    sample_digits = digits(inputs[0])
    input_digits = [set(digits(b)[j] for b in inputs) for j in range(5)]

    viable = {}
    for j in (0, 1, 2):
        viable[j] = {(k1, k2) for k1 in range(9) for k2 in range(9)
                     if len({O[k2][O[k1][v]] for v in input_digits[j]}) == 1}

    buckets = defaultdict(list)
    for v in reach:
        d = digits(v)
        buckets[(d[0], d[1], d[2])].append(v)

    gates = []
    for k1v in reach:
        d1 = digits(k1v)
        allowed0 = {k2 for (x, k2) in viable[0] if x == d1[0]}
        allowed1 = {k2 for (x, k2) in viable[1] if x == d1[1]}
        allowed2 = {k2 for (x, k2) in viable[2] if x == d1[2]}
        if not allowed0 or not allowed1 or not allowed2:
            continue
        for k20 in allowed0:
            for k21 in allowed1:
                for k22 in allowed2:
                    for k2v in buckets.get((k20, k21, k22), ()):
                        d2 = digits(k2v)
                        B = from_digits([O[d2[j]][O[d1[j]][sample_digits[j]]]
                                         for j in range(5)])
                        A = from_digits([O[d2[j]][O[d1[j]][eof_digits[j]]]
                                         for j in range(5)])
                        if A == B:
                            continue
                        gates.append((depth[k1v] + depth[k2v], k1v, k2v, A, B))
    gates.sort()

    cand_block = {a - 1 for a in SAFE_ZONE}
    assert {tuple(digits(a)[3:]) for a in cand_block} == {(8, 3)}

    byd34 = defaultdict(list)
    for v in reach:
        d = digits(v)
        byd34[(d[3], d[4])].append(v)

    def preimg(col, t):
        return [y for y in range(9) if col[y] == t]

    seen = set()
    hits = []
    scanned = 0
    no_s34 = 0
    for cost, k1v, k2v, A, B in gates:
        if (A, B) in seen:
            continue
        seen.add((A, B))
        dA, dB = digits(A), digits(B)
        s3 = set(preimg([O[y][dB[3]] for y in range(9)], 8)) & \
             set(preimg([O[y][dA[3]] for y in range(9)], 8))
        s4 = set(preimg([O[y][dB[4]] for y in range(9)], 3)) & \
             set(preimg([O[y][dA[4]] for y in range(9)], 3))
        if not s3 or not s4:
            no_s34 += 1
            continue
        for p3 in s3:
            for p4 in s4:
                for yf in byd34.get((p3, p4), ()):
                    scanned += 1
                    td = opw(B, yf)
                    if td not in cand_block:
                        continue
                    te = opw(A, yf)
                    if te in cand_block and te != td:
                        hits.append((cost + depth[yf], cost, k1v, k2v, A, B,
                                     yf, td, te))
    hits.sort()
    stats = {"gates": len(gates), "unique_classes": len(seen),
             "no_preimage": no_s34, "scanned_yf": scanned, "hits": len(hits)}
    return stats, hits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stored", action="store_true",
                        help="gate on op(byte,29524), not on the raw byte")
    args = parser.parse_args()
    with open(Path(__file__).parent / "k2_reach_full.pkl", "rb") as f:
        depth = pickle.load(f)["depth"]
    stats, hits = search(depth, stored=args.stored)
    print(f"EOF=59048 base9={digits(59048)}")
    print(f"gate input: {'op(byte,29524)' if args.stored else 'raw byte'}")
    print(f"search stats: {stats}")
    print("ALGEBRA_ONLY: routing, scratch rearming and executable K2 are NOT_DEMONSTRATED")
    for h in hits[:60]:
        tc, cost, k1v, k2v, A, B, yf, td, te = h
        line = (f"total~{tc} costs={cost}+{depth[yf]} K1={k1v} K2={k2v} A={A} B={B} "
                f"yf={yf}(d{depth[yf]}) echo_entry={td+1} halt_cell={te+1}")
        print("  " + line)

if __name__ == "__main__":
    main()
