# Window-tiling DP attack — k=18 streaming Cat (2026-10-24)

`STATUS`: structural search executed; **REFUTED as a path to >=118 ops**. The
7,331-operation k=18 floor of the current window mechanism stands.
`SCOPE`: BolgeForge streaming Cat (`artifacts/cat_compact.mal`, 7,972 cells, unchanged).
`ORIGIN`: profile of the winning k=18 plan motivated by the genealogy audit
(`GENEALOGIA_MALBOLGE`, Autobolge "Shapes"/position-arithmetic idea: derive the
partition algebraically instead of by seed restarts).

## Files

- `dp_synth.py` — instrumented copy of `k18_attack/search_synth.py` (MOVE_LOG per
  `set_dest_94_direct`, WIN_CALLS per window strategy, PHASE markers). Reproduces
  the documented 7,331 ops for seed 9803 exactly.
- `run_profile.py`, `profile_seed9803.txt` — the cost breakdown (raw output kept).
- `dp_synth2.py` — dp_synth + `window_cap` and `tiling` parameters (tiling = explicit
  partition of `sorted_addrs`; windows may exceed the cap; offset-0 writes allowed).
- `tiling_search.py`, `tiling_search_out.txt` — the local search (raw output kept).

## 1. Profile of the 7,331-op plan (seed 9803, borrow_penalty=1, direct_gap=18, restart 0.80/0.90)

| Phase | Ops |
| --- | --- |
| Boot (frozen handoff prefix contract) | 1,367 |
| Base moves (13 step9 = 299 + 2 direct = 118) | 417 |
| 16 windows (5,293 of it = per-write `solve_sp`+walk+ret machinery) | 5,458 |
| Final handoff (frozen contract) | 89 |
| **Total** | **7,331** (budget 7,213, gap +118..120) |

Facts that pin the structure:

- The 121 targets are almost contiguous: consecutive-gap histogram `1:112, 2:5, 3:1,
  11:1, 68:1`. Runs: 58,844-58,913, 58,924-58,978, 59,046-59,048.
- With a cap-9 window (offsets 1..9) and base = first-target-minus-1, a tiling of a
  contiguous run is forced up to boundary wobble of +-1 target.
- Per-write cost is dominated by the `solve_sp` A-computation (~30-45 ops), not by the
  offset walk (offset-1 NOPs are ~5 ops on average: offset histogram
  `1:633 2:506 3:649 4:565 5:543 6:457 7:744 8:508 9:688` over 121 writes).

## 2. Search executed (true cost via the real simulator, not a model)

1. **Wider caps with greedy tiling**: cap 9 → 7,331; cap 10 → 7,781 (+450);
   cap 11 → 8,046 (+715). **REFUTED**: extra offset walk outweighs saved moves.
2. **Boundary local search at cap 9**: for each of the 15 internal window boundaries,
   shift +-1/+-2 targets in both directions, plus merges of adjacent windows (<=12
   targets). 89 neighbors; best neighbor 7,432 (`shift2@b11R`); **none beats 7,331**.
   The greedy tiling is a local optimum of this neighborhood.
3. **2,000-seed restart over the best tiling**: min 7,360 (seed 1420) — worse than
   greedy tiling + seed 9803 (7,331). Consistent with the earlier 10,000-seed bottom.

## 3. Verdict

- DP over window partitions/bases: **REFUTED** for recovering >=118 ops. The tiling
  is essentially forced by target contiguity; the cost lives in the per-write
  `solve_sp` machinery, which the partition cannot touch.
- Micro-levers measured by hand from the profile (direct->step9+shifted window at
  the 11-gap ~ -13; cap-10 tiling ~ -16 net): combined well under the 118 gap.
- Remaining untested structural candidate (NOT_DEMONSTRATED, no evidence of gain):
  multi-target "chain sweeps" — writing several consecutive targets in one d-walk
  using the evolving `a` of consecutive CRZ ops, which requires
  `t_i = crazy(t_{i-1}, m_i)` alignments that the fixed target table rarely offers.

## 4. Consequence

`artifacts/cat_compact.mal` (7,972 cells) remains the published artifact; claim
"< 7,972 streaming Cat" stays **OPEN** with frontier k=18 7,331/7,213. Raw outputs:
`profile_seed9803.txt`, `tiling_search_out.txt`.
