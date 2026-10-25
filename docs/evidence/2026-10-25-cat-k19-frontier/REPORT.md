# k=19 frontier attack — order + spindle-assignment levers exhausted at +108

**Date:** 2026-10-25 · **Status: k=19 NOT FIT via this route — measured frontier 7,227 ops vs the 7,119 budget (+108).**
Scope: a k=19 streaming Cat would be **7,596 cells** (9,382 − 94·19, −94 vs the
published 7,690-cell k=18 artifact). The k=19 op budget is
`end_c = 99 + ops − 1 ≤ 9,003 − 1,786 = 7,217` → **ops ≤ 7,119**; with the
compact boot (1,235) and the handoff JMP (1) fixed, the write phase must fit
**≤ 5,883 ops**.

## 1. Claims

| claim | status |
|---|---|
| The write phase is k-invariant | **REFUTED** — 59/121 targets carry main-loop pointers (values shifted by −delta); their `a_req` set changes with k |
| A k=19 plan built from the k=18 demand sequence works | **REFUTED** — assembles in budget (end_c 7,208 ≤ 7,217) but halts at cell 7,391 with 60/124 variables: it installs k=18-shifted pointers |
| The z-entry cache model predicts the beam gain | **REFUTED** — predicted −433 (k18) / −255 (k19); the real-machine beam gives −89 / −192 / −158; the greedy's live-`a` entry already harvests most of the cache value |
| The spindles act as an `a_req` cache (`x_in` of a demand equals the previous `a_req` served on that spindle) | **MOSTLY DEMONSTRATED** — 78/94 chained (k18), 85/94 (k19, seed 9803), 16 breaks |
| The seeded-order lever fits k=19 | **REFUTED** — best of 10,000 seeds: 7,385 total (0 fits) |
| The best order + the fixed-order beam fits k=19 | **REFUTED** — best 7,227 (+108) |

## 2. The k-invariance falsification (why the first candidate died)

`w1_demand.py` extracts the demand sequence at any k. The 121 window targets
include **59 whose value points into the main loop** (reference values in
(9,003, 9,382), installed as `value − delta`): at k=18 they are
7,332..7,677, at k=19 they must be 7,238..7,583. A k=19 candidate assembled
from the k=18 sequence (`verify_k19.py` S1–S3) stays inside the cell budget
but the interpreted program jumps to k=18 addresses and **halts at cell 7,391,
step 7,111, with 60/124 handoff variables installed** — the 59 stale pointers
are exactly the divergence. Every k needs its own demand sequence.

Measured consequence: the k=19 greedy write phase (seed 9803) is **6,368 ops**
vs k=18's 5,963 (**+405**) — the shifted targets land on harder `a_req` values.

## 3. Levers, measured on the real machine

All numbers come from replaying the real synthesizer state (`w2_beam.py`),
whose **greedy control reproduces the recorded plans exactly** — 5,963 (k18),
6,368 (k19, seed 9803), 6,149 (k19, seed 9330); per-row length checks
121/121 writes, 13/13 plus9, 11–12/12 sweeps, 2/2 sd94, 1/1 final94.

| step | write ops | total | over budget |
|---|---:|---:|---:|
| greedy, seed 9803 | 6,368 | 7,604 | +485 |
| fixed-order beam-512 (spindle/entry per write) | 6,176 | 7,412 | +293 |
| 10,000-seed order sweep → best seed **9330** | 6,149 | 7,385 | +266 |
| beam-512 over seed 9330's order | **5,991** | **7,227** | **+108** |
| beam-512 over the next 6 best orders (3498/9509/485/6532/4482/8112) | 6,020–6,061 | 7,256–7,297 | +137…+178 |

Convergence evidence: at k=18 the beam saturates at width 512 (512 and 2048
both give 5,874); at k=19 the gains per order vary −108…−192 and the best
combined point is seed 9330 + beam = 7,227. A beam-2048 run on seed 9330 did
not complete (recorded as a limitation; the k=18 convergence data makes a
−108 recovery from width alone unlikely).

The beam explores all six (spindle, entry) choices per write over the fixed
greedy order with true-state deduplication — no cost model. The z-entry model
(`w1_demand.py` §model) that promised −433/−255 is refuted by these runs: the
greedy's live-`a` entry already captures most of the cache value.

## 4. Machinery (reusable, validated)

- `w1_demand.py --k K --seed S --tag T` — extracts the complete demand
  sequence (writes with `a_req`/preclear/base, plus9/sd94/reset94/sweep/
  final94 in execution order); the row accounting closes exactly against the
  emitted ops (5,963 + JMP = 5,964 at k=18).
- `w2_beam.py --beam N --demand D --out O` — greedy control + real-state
  beam; the control must match the demand file's accounting exactly.
- `sweep_k19.py` — seeded-order sweep via the canonical pipeline
  (`tools.resynthesize`, `boot="compact"`).
- `verify_k19.py` — full acceptance gates for any k=19 candidate (budget,
  assembly, canonical handoff comparison, post-handoff low-memory trace,
  mb_ref battery with `--full`).

## 5. Reproduction

```bash
python3 docs/evidence/2026-10-25-cat-k19-frontier/w1_demand.py --k 19 --seed 9330 --tag _k19s9330
python3 docs/evidence/2026-10-25-cat-k19-frontier/w2_beam.py \
  --demand docs/evidence/2026-10-25-cat-k19-frontier/out_demand_k19s9330.json \
  --out docs/evidence/2026-10-25-cat-k19-frontier/out_beam_k19s9330_ops.txt --beam 512
python3 docs/evidence/2026-10-25-cat-k19-frontier/sweep_k19.py --seeds 10000
```

Raw outputs: `out_w1*.txt`, `out_demand*.json`, `out_simlens.json`,
`out_sweep_k19.txt/json`, `out_beam*.txt`, `out_topseeds_beam.txt`,
`out_beam*.ops.txt` (the op streams), `out_verify*` (the failed first
candidate's gates).

## 6. Limits

- 10,000 seeds is a finite sample; the beam explores the (spindle, entry)
  space at fixed order only; no joint order+assignment search was run.
- The beam-2048 limitation on seed 9330 (did not complete) is recorded;
  k=18 evidence says width 512 already saturates.
- All results are for this synthesizer's plan structure (boot + per-target
  writes + forced sd94/final94); they say nothing about fundamentally
  different encodings.

## 7. Next experiments (ranked by expected value)

1. **Shorten the boot** (1,235 ops, asserted-correct but not proven minimal):
   the compact boot still contains verbatim segments (steps 1..59, 485..567,
   948..1005, 1342..1434) that were never BFS-optimized. The rotor precedent
   (51 → 27 ops) saved 24 ops on 3 cells; k=19 needs **−108 more from the
   boot** (budget: boot ≤ 1,127 at write 5,991). Same technique, larger
   scope: segment-level BFS preserving the liveness set (the write phase's
   spindle/odometer/anchor cells).
2. Joint window-level search (order + spindle assignment together) — bigger
   build, no measured bound.
3. A cheaper `a_req` metric — no mechanism identified; chain sweeps,
   window-tiling DP, the m1 `*jo` register and the spindle-cache policy are
   all measured and capped.

The 7,690-cell k=18 artifact (`artifacts/cat_compact.mal`, SHA-256
`0e14c807…`) is untouched by this experiment.
