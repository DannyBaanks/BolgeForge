# Compact streaming Cat: 7,972 cells with the reference handoff state

Date: 2026-10-24 · Artifact: `artifacts/cat_compact.mal` (7,972 cells, SHA-256
`0d298645…`) · Generator: `tools/build_compact_cat.py` · Raw numbers:
[`measurements.json`](measurements.json), [`handoff_state.json`](handoff_state.json)

## 1. The question

The verified `artifacts/cat_compressed.mal` streams input exactly in 8,254 cells. Is a smaller
Classic streaming Cat reachable with the *working* synthesizer, rather than with the broken
2026-10-19 pilot (which never installed the reference variable table)?

Answer: yes — **7,972 cells**, 282 fewer than the compressed Cat (3.4%) and 1,410 fewer than the
9,382-cell reference (15.0%), with the reference handoff state reproduced cell for cell.

## 2. Why the frontier moved

`tools/resynthesize.py` builds a preamble that reproduces the reference state at a jump cell and
then keeps the shifted suffix. The file is always `9,382 − delta` cells, so the only lever is
`delta = 94k`; the preamble must fit before the shifted handoff cell.

The generic search stops at **k=12** (8,254 cells). A sweep of `k = 12..40` (same parameters as
the published rebuild: borrow penalty 8, direct-jump threshold 27) shows every larger `k` missing
the budget. Two cheap changes shrink the preamble:

| change | k=15 preamble ops | gap to fit |
|---|---:|---:|
| historical (penalty 8, threshold 27) | 7,644 | +150 |
| direct window jumps (threshold 9) | 7,611 | +117 |
| borrow penalty 2 | 7,546 | **+52** |
| + seeded restart of the write order (seed 47) | **7,443** | **−51** |

At k=15 the shifted handoff cell is 7,593, the budget is 7,494 operations, and the chosen
preamble ends at cell 7,541 with 52 padding cells. The plan is deterministic: seed 47, borrow
penalty 2, direct gap 9.

The sweep also shows why k=15 and not something larger: the operation count stays near 7,200–8,000
because the 121 variable writes dominate, while the budget shrinks by 94 per step. k=16 would need
471 fewer operations; the measured k=24 low (7,164) still misses its 6,648 budget by 516.

## 3. Verification

* **Repo battery** (`tools/test_compressed.verify_target("cat", …)`, 7 cases): empty, `A`, `ABC`,
  `ABCD`, `Hello BolgeForge\n`, all 256 bytes, all 256 bytes ×16. Byte-exact, strict HALT, exit 0,
  no stderr — verified before publication and again by `--check`.
* **Extended battery** (8 cases, byte-exact against `reference/malbolge_org/cat.mal`): empty,
  1 byte, all 256 bytes, 4,096 bytes, 64 KiB zeros, 64 KiB random, 60 KB text, 10 KB newlines.
* **Long stream control** (unit test): 64 KiB of `random.Random(2026)` bytes matches the reference.
* **Handoff state** (`tools/verify_handoff_state.py`, `keep-high`): candidate reaches cell 7,657
  at step 7,530 with `a=29,524`, `d=58,975`; the reference reaches cell 9,067 at step 8,992 with
  the same registers; **124/124** modified cells above the image are installed with the shifted
  values.
* **Deterministic rebuild**: `python3 tools/build_compact_cat.py --check` reproduces the published
  bytes exactly.
* **Regression**: `make test` → 52 tests OK (was 38 before this change); `make test-rebuild`
  still rebuilds the four published compressed artifacts byte for byte.

## 4. Gate correction: two layouts, not one

The 2026-10-23 gate assumed that a compacted program moves *everything* down by `delta` — the
program counter, the `d` register and the high-memory variable table. That is not how
`tools/resynthesize.py` works: only the program image moves; the high-memory workspace stays at
its original addresses, and only values that address the shifted suffix are decremented.

The gate now models both layouts and defaults to `keep-high`. The control that settles it:

```
$ python3 tools/verify_handoff_state.py --reference reference/malbolge_org/cat.mal \
    --reference-cell 9067 --candidate artifacts/cat_compressed.mal --delta 1128 \
    --value-floor 9003
variables installed: 124/124
HANDOFF MATCH

$ python3 tools/verify_handoff_state.py --reference reference/malbolge_org/cat.mal \
    --reference-cell 9067 --candidate artifacts/cat_compressed.mal --delta 1128 \
    --memory-mode shift-all
variables installed: 0/124
HANDOFF MISMATCH
```

So the published, byte-verified 8,254-cell artifact *fails* the old model. The 2026-10-23
conclusion about the pilot is unchanged — under `keep-high` the pilot still reaches its loop with
`a=29,521` (want 29,524), `d=97` (want 58,975) and 0/124 variables — but its "required d = 57,377"
figure was an artefact of the wrong layout. The correct required value is 58,975. See the erratum
appended to `docs/evidence/2026-10-23-compact-cat-diagnosis/REPORT.md`.

## 5. Rejected paths

| path | measurement | why rejected |
|---|---|---|
| wider write windows (12–30 cells) | 8,400–9,526 ops | NOP offsets cost more than the saved `d` moves |
| 2-step lookahead ordering | 7,615 ops at k=15 | worse than the tuned greedy (7,546) |
| searching all `sp` bases for the final `d` setup | 7,532 ops | trailing walk is tuned to the 71-base; `assert d == handoff_d` fails at other penalties |
| dropping dead cell 59,046 | 7,461 ops (fits) | changes the reproduced handoff state; not used |
| truncating the 10 dead tail cells | 10 cells | semantic change with no proof; not used |

## 6. Claims

| claim | status | evidence |
|---|---|---|
| A Classic streaming Cat of 7,972 cells exists | **DEMONSTRATED** | `artifacts/cat_compact.mal`, SHA-256 `0d298645…`; exact-output battery above |
| It is 282 cells (3.4%) smaller than `cat_compressed.mal` | **DEMONSTRATED** | `tests/test_compact_cat.py`; `measurements.json` |
| It reproduces the reference handoff state | **DEMONSTRATED** | `tools/verify_handoff_state.py` `keep-high`, 124/124 |
| It is the smallest reachable Cat | **NOT_DEMONSTRATED** | only the plans in this report were measured |
| It is equivalent to the reference on every input | **NOT_DEMONSTRATED** | finite testing (17 cases), same standard as the other compressed artifacts |
| The 2026-10-23 gate used the layout of the working compressor | **REFUTED** | `cat_compressed.mal` reports 0/124 under `shift-all` |

## 7. Reproduction

```
python3 tools/build_compact_cat.py --check     # rebuild + verify + compare published bytes
python3 tools/build_compact_cat.py             # rebuild + verify + publish
python3 -m unittest tests.test_compact_cat -v  # 5 certification tests
make test                                      # 52 tests, corpus, compressed, quines, mirror
```

Plan: `k=15`, `delta=1,410`, seed 47, borrow penalty 2, direct gap 9; preamble 7,443 operations,
end cell 7,541, padded to the handoff at 7,593, suffix from 9,004.
