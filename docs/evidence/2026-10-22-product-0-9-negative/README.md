# Native product 0..9 - address-packing blocker

Status: **NOT_DEMONSTRATED**. This directory records why the verified native
`square(0..9)` dispatcher was not extended to a native `product(0..9)`. There is
no product artifact.

## Question

Can the native runtime dispatcher used by
`experiments/square_0_9_native_dispatcher/` be extended to `product(a,b)` for
`a,b in 0..9`?

## Result

No, under the current bootstrap/branch architecture.

The bootstrap computes a row state `S_d`. The transfer block at `S_d+1` is
`p j j i`, and its `p` always reads `mem[50]=48`. The recipe address is
therefore `op(S_d,48)`. Changing `mem[50]` is not available: an exhaustive scan
over printable constants `33..126` found that only `48` reaches `S_3+1` with the
expected `(a,d,mem[50])` state.

`op(x,48)` is not injective. A 10-set construction can place 100 distinct
addresses with minimum gap 27 before the branch, but after the mandatory
`op(...,48)` only **56** addresses remain distinct and the minimum gap is **0**.
Without 100 distinct, spaced addresses the 100 recipes cannot be laid out
disjointly.

## Evidence

Environment: Linux `7.0.0-38-generic` x86_64, Python `3.12.3`, UTC
`2026-10-22T21:24:31Z`.

Command:

```bash
cd "$(git rev-parse --show-toplevel)"
python3 docs/evidence/2026-10-22-product-0-9-negative/check_product_block.py
```

Output:

```json
{
  "bootstrap_c50_working": [
    48
  ],
  "packing_after_branch": {
    "count": 100,
    "max": 28831,
    "min": 48,
    "min_gap": 0,
    "unique": 56
  },
  "packing_before_branch": {
    "count": 100,
    "max": 51759,
    "min": 1458,
    "min_gap": 27,
    "unique": 100
  },
  "transform_sets": 10,
  "verdict": "NOT_DEMONSTRATED"
}
```

Exit status: `0`. The script asserts the three reproduced facts above and exits
nonzero if any of them changes.

The 10 transformation sets used before the branch are:

```text
(r1, c, r2) =
(1, 95, 6) (1, 98, 7) (3, 121, 4) (1, 125, 5) (2, 122, 7)
(3, 67, 6) (0, 53, 6) (3, 67, 5) (3, 64, 7) (3, 67, 4)
```

with `Q = rot^r2(op(rot^r1(S), c))` and the row state set

```text
S = [28471, 28444, 28498, 28633, 28606, 28660, 28795, 28768, 28822, 28714]
```

## Control

The native square control remains green:

```text
0: '0\n' HALT
1: '1\n' HALT
2: '4\n' HALT
3: '9\n' HALT
4: '16\n' HALT
5: '25\n' HALT
6: '36\n' HALT
7: '49\n' HALT
8: '64\n' HALT
9: '81\n' HALT
artifact=native_square.mal bytes=39406 sha256=6026ddc03133c824d821dcc5b779fce414fd07c2e3d3c8591b8bcaadcbcfd6d0
cells=59049 builder=build_native_square.py
```

## Semantics correction

Earlier exploration modeled `*` as rotating the accumulator. In Classic
Malbolge, `*` sets `a = mem[d] = rot(mem[d])`; the result depends on the
constant cell, not on the current accumulator. The 100-key hash and the row
sequence packings from that exploration are therefore not implementable and are
retracted. No artifact from those constructions is included here.

## Claims

| Claim | Status | Scope |
|---|---|---|
| Native `square(0..9)` produces `d*d` for all ten digits | **DEMONSTRATED** | Separate evidence in `experiments/square_0_9_native_dispatcher/` |
| Native `product(0..9)` exists | **NOT_DEMONSTRATED** | No artifact |
| 100 distinct recipe addresses survive the fixed branch | **REFUTED** | 56 unique, minimum gap 0 |
| The bootstrap accepts a printable `mem[50]` other than 48 | **REFUTED** | Exhaustive `33..126`; only 48 reached `S_3+1` |
| Prior 100-key hash / row packings are implementable | **REFUTED** | Based on incorrect `*` semantics |
| All possible product layouts are impossible | **NOT_DEMONSTRATED** | Only this bootstrap/branch architecture was tested |

## Limits

- This is an address-packing blocker, not a proof that no Malbolge product is
  possible.
- The disjoint-set search was randomized, not exhaustive. Only the `mem[50]`
  scan over printable constants was exhaustive.
- No product artifact, generator, tests or multi-digit evidence exist.
- The square artifact is the only verified runtime result in this record.

## Reproduce

```bash
cd "$(git rev-parse --show-toplevel)"
python3 docs/evidence/2026-10-22-product-0-9-negative/check_product_block.py
python3 experiments/square_0_9_native_dispatcher/verify_native_square.py
```

Both commands must exit `0`.
