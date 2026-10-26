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

## 8. Boot attack (2026-10-25, later) — measured, capped at -22 verified

The ranked next experiment was shortening the boot (1,235 ops, needed -108).
Machinery and findings (all in this directory):

| probe | result |
|---|---|
| `i` ops anywhere in the boot | **0** — the boot is a pure (a, d, mem) program, any segment re-synthesizable |
| op composition | 687 `o` (55%), 246 `j`, 163 `*`, 139 `p`; verbatim segments total 476 ops |
| dead stores (writes never read) | ~0-1 per segment — the boot is route-dense: nearly every cell in [32..96] is a live jump anchor |
| **NOP-run compression** (`nop_compress.py`) | **-22 ops, VERIFIED**: each maximal NOP run is memory-frozen, so a `j` can skip it when a cell holds exactly (later position − 1); boundary equivalence asserted at every op (7,146 checks) + final memory identical |
| end-to-end validation | the compressed k=18 plan (7,199 → 7,177) assembles, handoff 124/124, `mb_ref` 7/7 — the compression is publishable-grade |
| segment BFS with writes (`boot_bfs.py`) | naive layered BFS over {o,j,*,p} hits the 4M-state cap at depth 46 on segment A without beating 59 — needs A* with a (live-mismatch + d-distance) heuristic, not more width |
| liveness precision | LIVE-at-boot-end = 35 cells {32..39, 47..55, 70..78, 80..96}; cells 76..79 are dead at boot end but sit *behind* the return point d=82 — geometry-unfavorable as free anchors |

Net for k=19: 7,227 → **7,205** (with the JMP) vs the 7,119 budget — **+86 remain**.
The boot's 687 NOPs are mostly irreducible walks between live route anchors; the
4 compressible runs were worth 22 ops. The remaining levers are (a) A* segment
re-synthesis with anchor *creation* (rotating dead cells mid-boot to build jump
shortcuts, the architecture the boot already uses internally), and (b) the
write-phase entry pads (~4 ops × ~180 spindle entries): both are re-architecture
with unbounded effort, not tuning.

## 9. A* segment re-synthesis (2026-10-25, latest) — boot 1,235 -> 1,177, all verified

Root-cause found and fixed along the way: the liveness log recorded the
**post-op** d, so every `j` read was attributed to its *target* cell instead
of its *source* — route cells (e.g. cell 95) looked dead, the first A* batch
overwrote them and the chain broke at C9. With the pre-op-d log the live sets
are correct (LIVE at boot end grows from 28 to 41 cells).

| step | result |
|---|---|
| A* over ops {o,j,*,p}, goal = (d, a, live cells), dead cells free, heuristic = live-mismatch + reverse-BFS d-distance (`boot_astar.py`) | 9 verbatim segments compress: 476 -> 436 ops (**-40**); the 6 big segments and the handoff's custom parts (rotor/p1/p2) cap out at 400k expansions |
| splice + chain validation (`boot_splice.py`) | **EQUIVALENCE PASS**: new boot (1,195) + the ORIGINAL write ops reach the byte-identical final state (a, d, full memory); zero re-searches needed |
| NOP-run compression re-applied | boot 1,195 -> **1,177** |

**k=19 scoreboard after this session** (budget 7,119; write = seed-9330 + beam-512, 5,991 ops):

| stage | k=19 total | over budget |
|---|---:|---:|
| greedy order (seed 9803) | 7,604 | +485 |
| 10,000-seed sweep (best 9330) | 7,385 | +266 |
| + beam-512 spindle/entry assignment | 7,227 | +108 |
| + NOP-run compression | 7,205 | +86 |
| + A* segments (-40) | 7,187 | +68 |
| + NOP compression of the new boot | **7,169** | **+50** |

The k=18 plan with the new boot is 7,159 (budget 7,213, margin 54) with the
same 7,690-cell artifact size — the new boot is publishable-grade but changes
no claim (artifact size depends only on k).

Remaining levers for the last 50 ops: higher A* caps on the big segments
(running), the write-phase entry pads (~4 ops x ~180 spindle entries,
requires coordinated re-anchoring of cells 84..86 + planner templates), or a
joint order+assignment search.

## 10. BREAKTHROUGH (2026-10-25, night) — k=19 FITS: the 7,596-cell Cat

**DEMONSTRATED**: `out_k19_candidate.mal`, **7,596 cells** (9,382 − 94·19;
−94 vs the published 7,690 k=18 artifact, −1,786 vs the reference),
SHA-256 `80b9dca9af6427135da41ffe2131fad0b5c6ffc1b4b92c8d832d5ebe1911afb9`.
Plan: **7,056 ops vs the 7,119 budget (margin 63)**.

### 10.1 The joint search (m2): order x assignment together

`w3_joint.py` keeps a beam over (memory, a, remaining-writes) per window and
chooses, per state, WHICH target to write next and with WHICH (spindle,
entry) — control: at fixed order and width 512 it reproduces w2's 5,991
exactly. Joint beam-128: write phase **5,883 ops** (−108).

### 10.2 THE SEMANTIC TRAP: `i` encrypts its jump destination

The first A* batch was model-equivalent yet broke at runtime. Root cause
found by op-by-op model-vs-real lockstep tracing: **Classic Malbolge
encrypts the cell an `i` jumps TO** (it is in mb_ref.c's own comment —
"Jump encrypts its destination" — and in the canonical interpreter). The
entry template's `i` at cell 0 jumps to cell 98 and encrypts it: at runtime
cells 0 and 98 differ from the planner model before any plan op runs. The
canonical plans never read them (empirically proven by 7,199/7,199
lockstep on the published k=18 candidate); my A* guard allowed reads up to
98 and S7's found path read cell 98. **Fix**: reads restricted to
[1..97] ∪ [58,843..59,048]. After the fix the spliced boot holds a
**7,160/7,160 model-vs-runtime lockstep** — the A* savings are now
runtime-proven, not model-proven. (A second, earlier liveness bug — the
log recorded the post-op d, attributing each `j` read to its target cell —
was also found and fixed this session.)

### 10.3 The final chain (every step deterministic, every op verified)

| step | ops |
|---|---:|
| compact boot (canonical) | 1,235 |
| A* segments (9 replacements, runtime-safe guard) | 1,196 |
| joint write phase (beam-128, order x assignment) | 5,883 |
| JMP + NOP-run compression | 7,056 total |

Gates: assemble end_c 7,154 ≤ 7,217; handoff **124/124, AT_CELL, 0
mismatches, registers equal** (the compare requires the reference memory
mutated to its handoff state — a 0/0 result means a misuse of the gate);
`mb_ref` 7/7 cases; **64 KiB binary 65,536/65,536 exact**; traced echo
2,048/2,048 exact with **zero post-handoff low-memory reads** (the safety
property for both the boot's A* deltas and the joint write stream).

### 10.4 k=19 scoreboard (all levers measured this session)

| stage | k=19 total |
|---|---:|
| greedy order (seed 9803) | 7,604 |
| 10,000-seed sweep (best 9330) | 7,385 |
| + fixed-order beam-512 | 7,227 |
| + NOP compression | 7,205 |
| + A* segments (first, broken guard) | 7,187* |
| + A* runtime-safe + joint beam-128 + compression | **7,056** |

Not yet done: the publication pipeline (replace `artifacts/cat_compact.mal`,
wire the deterministic chain into `tools/`, update tests/CLAIMS/ROADMAP/
README, full `make test` + independent mirror). The 7,690-cell artifact is
untouched; this candidate is evidence-grade, verified by every research
gate the repository uses.
