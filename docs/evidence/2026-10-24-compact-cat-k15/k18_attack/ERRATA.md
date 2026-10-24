# Errata — k=16/k=18 attack and the "two dead cells" refutation

Date: 2026-10-24 (later than the parent report) · Status: **no new artifact published**
Parent evidence: [`../REPORT.md`](../REPORT.md), [`../measurements.json`](../measurements.json)

This note records a failed attack on the 7,972-cell frontier and the refutation of the
"two dead cells" shortcut that would have produced a 7,690-cell artifact. It does not
modify the parent report; the published artifact remains `artifacts/cat_compact.mal`
(7,972 cells, SHA-256 `0d298645…`).

## 1. The shortcut that was tried

A liveness probe run from the reference handoff (cell 9,003) reported that only cells
`58,844` and `59,046` are never read or executed, and concluded that a plan omitting
them could be built. With the omitted cells and a relaxed write-order search
(borrow penalty 2, direct gap 18, restart thresholds 0.80/0.90, seed 1435) the
synthesizer produced a **7,210-operation** preamble at k=18 — inside the 7,213-operation
limit — i.e. a 7,690-cell program.

## 2. Refutation — both cells are live

Build and run (`patch_liveness.py`, kept in this directory):

```
candidate: cat_7690_119.mal cells=7690 preamble_ops=7210 end_c=7308
patch=()              result=INVALID 58844 29443  step=28
patch=(58844,)        result=AT_CELL  step=86  a=OK d=OK variables=123/124
patch=(58844, 59046)  result=AT_CELL  step=86  a=OK d=OK variables=124/124
```

* Without the two cells the real interpreter (`oracle/mb_ref.c`, exit 3) dies with
  `INVALID_ENCRYPTION: cell 58844 value 29443` at step 7,239. The shifted suffix reaches
  cell 58,844 and executes it; the reference value there is 81 (printable), the candidate's
  fill is 29,443.
* Patching only `58,844` reaches the gate cell 7,375 with `a=29,524`, `d=58,975`, but one
  of the 124 compared cells is wrong.
* Patching both `58,844=81` and `59,046=109` (their reference values at cell 9,003) reaches
  the gate with `a=29,524`, `d=58,975` and **124/124** variables via
  `compare_handoff(..., memory_mode="keep-high")`.

The earlier liveness probe was wrong for this path: it started from the 9,003 handoff
state and halted at cell 9,025, so it never followed the branch the shifted suffix takes
through the boot-tail self-modification. **No handoff exemption is legitimate**; the
strict gate needs all 124 cells.

Consequence: the 7,210-operation plan is invalid and must not be published. The 7,690-cell
candidate built from it is kept only as the negative control above.

## 3. Frontier with all 121 installed targets

Budgets: `ops <= 9,003 - 94k - 99 - 1` (the report's convention is one lower,
`8,904 - 94k`). All searches install all 121 `high_mods` from cell 9,003.

| k | cells | budget (strict) | deterministic (pen 1 / pen 2) | 2,000 seeded (min, pen 1 / pen 2) | gap at best |
|---:|---:|---:|---:|---:|---:|
| 16 | 7,878 | 7,400 | 7,853 / 7,871 | 7,624 / 7,612 | +212 |
| 17 | 7,784 | 7,306 | 7,841 / 7,861 | 7,704 / 7,694 | +388 |
| 18 | 7,690 | 7,213 | 7,643 / 7,712 | 7,360 / 7,391 | +147 |
| 15 (published) | 7,972 | 7,494 | — | 7,443 (seed 47) | **−51 (fit)** |

Seeded runs: 2,000 seeds per (k, penalty), restart thresholds 0.80/0.90. A 10,000-seed
run at k=18, penalty 1, found a minimum of **7,331** (seed 9803), still 118 over the
budget; no seed fit. Best ten: `(9803, 7331), (7073, 7358), (1420, 7360), (948, 7362),
(9041, 7375), (917, 7376), (4400, 7382), (6402, 7382), (4277, 7387), (4749, 7387)`.

Raw outputs and the exact scripts are in this directory:
`search_seeds_2k.py`, `search_seeds_10k.py`, `search_synth.py` (the synthesizer copy
with `restart_p1`/`restart_p2`; defaults `0.60`/`0.75` are unchanged, so the published
artifacts remain byte-exact), and `patch_liveness.py`.

## 4. Why the omission does not generalize

Adding the two cells back costs more than two writes: installing `58,844` moves the
first window base from `58,844` to `58,843`, shifting the whole partition. Deterministic
k=18 costs: both omitted 7,458; `59,046` only 7,528; `58,844` only 7,567/7,628; both
installed 7,643/7,712. The seeded 119-cell low (7,210) plus this mandatory cost lands
above the 7,213 budget.

## 5. Verdict

| claim | status | evidence |
|---|---|---|
| A 7,690-cell Cat built by omitting `58,844`/`59,046` works | **REFUTED** | section 2; `patch_liveness.py` |
| The two cells are dead / exemptable | **REFUTED** | section 2 |
| A streaming Cat smaller than 7,972 cells exists | **NOT_DEMONSTRATED** | section 3: best measured k=18 plan needs 7,331 ops (118 over) |
| The published 7,972-cell Cat is unchanged | **DEMONSTRATED** | parent report; no artifact touched by this attack |

The measured frontier is k=18 at 7,331 preamble operations (118 over budget). Closing it
needs a structural change (window partition optimisation or cheaper base moves), not a
larger seed search: 10,000 seeds did not move the floor below 7,331.
