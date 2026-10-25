# Chain sweeps — multi-target CRZ walks (Classic streaming Cat)

Date: 2026-10-25 · Status: **REFUTED as a path to the 118-operation gap.**
Scope: the k=18 write plan for `artifacts/cat_compact.mal` (7,972 cells,
unchanged) and its 121 installed targets.
Origin: the last untested structural candidate listed in
[`../2026-10-24-window-dp-v0/REPORT.md`](../2026-10-24-window-dp-v0/REPORT.md) §3:
*writing several consecutive targets in one d-walk using the evolving `a` of
consecutive CRZ ops.*

## 1. What a chain sweep is, exactly

The preamble installs 121 high-memory targets one at a time. Each write needs a
specific `a` before its CRZ (`p` does `mem[d] = crazy(a, mem[d]); a = mem[d]`),
and the current planner pays, per target:

```
[trip to the SP scratch: solve_sp -> a_req] + [d back into the window]
+ [NOP offset walk] + CRZ + [return to cell 82]
```

After the CRZ, `a` equals the value just installed. A chain sweep keeps walking
`d` forward and writes the next target with that inherited `a`, so a link
`i -> j` (address_i < address_j) is legal iff

```
targ_i == find_a_for_crazy(cur_j, targ_j)      (the value i installs is the a j needs)
```

The first target of a chain pays the normal `solve_sp` + walk; every following
target pays only `address_j - address_i - 1` NOPs plus one CRZ; the chain ends
with a single return to cell 82.

`chain_synth.py` in this directory is the k18 synthesizer copy
(`../2026-10-24-compact-cat-k15/k18_attack/search_synth.py`) with an opt-in
`chains=` parameter and `emit_chain()`, which asserts the link condition and the
final values at every step. It reproduces the published numbers exactly:
deterministic k=18 = **7,643** and seed 9,803 = **7,331** operations.

## 2. The alignment map — the fixed target table rarely offers a link

`alignment_map.py` / `out_alignment.txt`. From the fill state (the crazy
recurrence above the 9,382-cell image, i.e. what the preamble sees before it
touches a target):

| k | budget | usable pairs | adjacent pairs |
|---:|---:|---:|---:|
| 15 | 7,494 | 6 | 0 |
| 16 | 7,400 | 6 | 0 |
| 17 | 7,306 | 6 | 0 |
| **18** | **7,213** | **6** | **0** |
| 19–24 | 7,118–6,648 | 6 | 0 |

The six pairs (k=18, `delta=1,692`):

| i → j | value installed at i | gap (cells) |
|---|---:|---:|
| 58,864 → 58,881 | 29,524 | 17 |
| 58,864 → 58,896 | 29,524 | 32 |
| 58,881 → 58,890 | 0 | 9 |
| 58,881 → 58,931 | 0 | 50 |
| 58,890 → 58,896 | 29,524 | 6 |
| 58,896 → 58,931 | 0 | 35 |

No adjacent pair, and the map does not change with `k`. In addition **61 of the
121 targets have no CRZ preimage from their fill value** (they are pre-cleared by
the window strategy); those cells cannot be link endpoints before the pre-clear,
and a chain cannot both pre-clear and install a cell in one ascending pass.

## 3. Measurements (exact simulator, deterministic)

`measure_chains.py` / `out_measure.txt`:

| plan | operations | delta |
|---|---:|---:|
| baseline, deterministic (rng=None) | **7,643** | — |
| baseline, seed 9,803 (published frontier) | **7,331** | — |
| five-target chain 58,864→58,881→58,890→58,896→58,931 | 7,667 | **+24** |
| pair 58,890 → 58,896 | 7,627 | **−16** |
| pair 58,884 → 58,893 | — | invalid at chain time: 58,893 needs a pre-clear |
| pair 58,890 → 58,896, seed 9,803 | 7,589 | +258 |

The five-target chain costs **75** operations as a block against **61** for the
same five writes emitted separately in the baseline plan (+14 gross; the block
walks 67 cells to reach 58,931, while each separate write walks at most 9 from
its own window base). The only chain that wins is the short pair 58,890→58,896
(12 operations vs 28 separate, −16).

The per-write profile explains why:

| class | targets | operations |
|---|---:|---:|
| expensive writes, ≥ 25 ops | 98 | 4,969 |
| cheap writes, ≤ 15 ops | 5 | 61 |

All six aligned pairs involve cheap writes (7–14 ops). The expensive writes —
where the `solve_sp` cost actually lives — have no alignment at all.

## 4. Why the route cannot close the 118-operation gap

A link `i -> j` exists exactly when the value installed at `i` equals the `a`
required at `j`. In that situation the *existing* per-write planner can also
write `j` immediately after `i`: `compute_and_jump` degenerates to
`NOP + DLD + DLD` (3 operations) because `a` already matches. So a chain never
removes the expensive `solve_sp`; it only replaces
`return_i + 3 + offset_walk_j` with the direct gap walk, a saving of roughly
`ret_i + 3 + address_i − base_j` — about 10–20 operations, and negative when the
targets sit in different windows (as in the five-target chain).

With six pairs, zero adjacent pairs and one usable disjoint link, the total
available gain is on the order of the measured **16 operations** (a loose
upper bound over all pairs is ~30), against a **+118** gap at k=18
(7,331 → 7,213). The structural candidate is exhausted:
chain sweeps rewrite the *walk*, but the 98 expensive writes account for 4,969
of the 5,416 write-phase operations and their cost is dominated by `solve_sp`,
which the alignment condition cannot touch.

## 5. Same-horizon seed control

`search_chains_10k.py` runs the identical 10,000-seed sweep as the published
frontier (`borrow_penalty=1`, `direct_gap=18`, restart 0.80/0.90) with the only
winning chain enabled. Raw output: `out_chain_10k.txt`.

```
k18 pen1 0.80/0.90 all121 + chain 58890->58896: min 7341 seed 5921
best10 [(5921, 7341), (2793, 7342), (6341, 7344), (3391, 7347), (6477, 7352),
        (8500, 7362), (487, 7363), (2982, 7367), (9117, 7367), (7197, 7369)]
fits 0
```

The baseline over the same horizon is **7,331** (seed 9,803, 10,000 seeds, no
fit). The chain changes the restart stream, so individual seeds move; the sweep
is a horizon control, not a paired comparison. It confirms that the +16
deterministic gain does not compound into a fit: the minimum stays 128
operations above the 7,213 budget.

## 6. Claims

| claim | status | evidence |
|---|---|---|
| The Cat target table admits multi-target chain links | **DEMONSTRATED** | six pairs, `out_alignment.txt` |
| A chain link removes the per-write `solve_sp` cost | **REFUTED** | link condition implies `a` already matches; §4 |
| The five-target chain saves operations | **REFUTED** | 75-op block vs 61 separate (+24 plan) |
| Chain sweeps can recover the 118-operation gap at k=18 | **REFUTED** | alignment map + per-write profile + 10k sweep |
| A streaming Cat smaller than 7,972 cells exists | **NOT_DEMONSTRATED** | frontier unchanged: 7,331/7,213 |
| `artifacts/cat_compact.mal` is unchanged | **DEMONSTRATED** | no artifact path touched; SHA-256 `0d298645…` |

Finite-testing limits: the alignment map is exhaustive over the 121 targets for
`k=15..24` under this synthesizer's fill model; the operation counts are from
the exact simulator used to build the published artifact. No new artifact was
produced, so no output battery was run.

## 7. Reproduction

```
python3 docs/evidence/2026-10-25-cat-chain-sweeps/alignment_map.py
python3 docs/evidence/2026-10-25-cat-chain-sweeps/measure_chains.py
python3 docs/evidence/2026-10-25-cat-chain-sweeps/search_chains_10k.py
python3 docs/evidence/2026-10-25-cat-chain-sweeps/cost_split.py
```

`chain_synth.py` is evidence-only: it is not wired into
`tools/build_compact_cat.py`, and the published artifact still rebuilds
byte-exactly from the untouched `tools/resynthesize.py`.

## 8. Consequence

The last untested structural candidate of the window-DP report is now measured
and refuted. The 7,972-cell artifact stands. A smaller Cat needs a cheaper way
to *compute* `a_req` (the `solve_sp` primitive, ~50 operations on average across
the 98 expensive writes), not a better way to walk between targets.

## 9. Errata 2026-10-25 — cross-check with the m1 limits work

Question raised after the `m1_limits` / `zig_synth` research (ISyCo monorepo,
`workspace/assembly/malbolge/analysis/`): the two-cell stationary register
(`*` at 154, `j` at 155, `o` at 153 — d cycles 154 → 155 → 153 → 154 and the
same cell rotates in place) and the `routefix` result (routes built on a memory
snapshot are invalid on live memory; a fresh BFS finds 4–5-op routes). Can
either close the 118-operation gap?

Measurement (`cost_split.py`, `out_cost_split.txt`) decomposes the published
seed-9803 plan (7,331 ops) with four bookkeeping hooks on `chain_synth.py`; the
synthesizer itself is unchanged.

| component | ops | share |
|---|---:|---:|
| 121 writes, `solve_sp` strings (`arith`) | 3,677 | 50.2% of the plan |
| 121 writes, entry pad + final DLD (`move`) | 583 | 8.0% |
| 121 writes, offset walk (`walk`) | 465 | 6.3% |
| 121 writes, return to 82 (`ret`) | 540 | 7.4% |
| boot solves (17 `BOOT_START_MAP` entries) | 531 | 7.2% |
| boot literal image (834 cells, 1 op each) | 834 | 11.4% |
| pre-clear domino sweeps + handoff (residual) | 580 | 7.9% |

Within the write phase (5,386 ops) the `a`-arithmetic is **68.3%**; all
d-movement together (`move + walk + ret`) is 1,588 ops, i.e. **~12 ops per
target**.

**Finding 1 — the gadget is op-for-op the solver's existing move.** The cost-3
move in `solve_sp_c` is `oj*` (rotate the tracked cell, 3 ops). `*jo` is also 3
ops and produces the same `(cell value → rot, a → rot)` transition; the only
difference is where `d` ends up, and every solver move re-establishes `d` with
its own `j`. Same cost, same reachable set: **no cheaper metric.**
*Labels: op-count equality DEMONSTRATED by counting the two sequences; identity
of the BFS state transition INFERRED from both sequences' op semantics.*

**Finding 2 — displacement is irreducible.** The only NOP run in a write is
`offset - 1` (the distance from the window base to the target): the CRZ must
execute *at* the target address, and no register moved `d` there. A stationary
rotor removes neither the walk nor the CRZ.

**Finding 3 — there is no stale-route defect to fix.** `BOOT_START_MAP` is the
only precomputed route table (hard-coded `targ_a` per interval, the `ROUTE_MEM`
analogue), and it costs 531 ops in 17 solves. Unlike the m1 case, there is no
staleness to recover: every step is replayed by `sim_ops` with assertions, the
handoff state reproduces 124/124, and each solve is already the BFS shortest
path *in the solver's metric*. The m1 defect made routes *invalid*; here the
routes are valid and optimal-in-metric, so `routefix` has nothing to reclaim.

**Consequence.** Neither mechanism touches the 68% that is `solve_sp`, and the
22% that is movement is ~12 ops/target of which the displacement is geometric.
**REFUTED as a route to the 118 operations** (scope: k=18 plan, published
geometry, this synthesizer). The m1 result still matters epistemically — it
proves a synthesizer frontier is not a language floor — but for the Cat the
frontier is already known to be a synthesizer frontier, not a Malbolge bound.

**One new measured fact.** The 121 writes use only **53 distinct `a_req`
values** (the top value, 29,544, appears 9 times; 94 writes share a repeated
value), and consecutive `a_req` are related by equality in 6 cases and by a
rotation in 0. Reuse is nevertheless blocked by the write itself: after a CRZ
`a` equals the *installed value*, not `a_req`, and the 6 equal cases are exactly
the chain links already refuted in §2–§3.
