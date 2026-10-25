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
chain sweeps rewrite the *walk*, but 92% of the write cost is the
`solve_sp` computation, which the alignment condition cannot touch.

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
```

`chain_synth.py` is evidence-only: it is not wired into
`tools/build_compact_cat.py`, and the published artifact still rebuilds
byte-exactly from the untouched `tools/resynthesize.py`.

## 8. Consequence

The last untested structural candidate of the window-DP report is now measured
and refuted. The 7,972-cell artifact stands. A smaller Cat needs a cheaper way
to *compute* `a_req` (the `solve_sp` primitive, ~35–50 operations per expensive
write), not a better way to walk between targets.
