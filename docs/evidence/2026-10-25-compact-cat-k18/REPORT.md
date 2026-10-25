# Compact Cat k=18 — 7,690 cells (compact BOOT, −132 ops)

**Date:** 2026-10-25 · **Status: DEMONSTRATED** (full battery below).
**Origin:** bridge handoff `antigravity_53501039` (ANNOUNCE seq=9040, RESULT
seq=9041; `HANDOFF_BOLGEFORGE_K18_7690_2026-10-25.md`), independently
verified and integrated here. The 7,972-cell k=15 artifact this supersedes
remains rebuildable from git history (its evidence:
[`../2026-10-24-compact-cat-k15/`](../2026-10-24-compact-cat-k15/)).

## 1. Claim

| claim | status |
|---|---|
| A streaming Cat smaller than the published 7,972 cells exists | **DEMONSTRATED**: `artifacts/cat_compact.mal`, **7,690 cells** (−282 vs 7,972; −564 vs the 8,254 compressed Cat; −1,692, 18.0%, vs the 9,382-cell reference), SHA-256 `0e14c807f288d01e17996024474e22395f581e50c1c14afb7b00dc8ec68df74b` |
| The k=18 plan fits the op budget | **DEMONSTRATED**: 7,199 preamble operations ≤ 7,213 (margin 14); `end_c` 7,297 ≤ 7,311 |
| The reference handoff state is preserved | **DEMONSTRATED**: `compare_handoff` keep-high, 124/124 variables, 0 mismatches, registers `a=29524, d=58975` equal to the reference at cell 9,067 |
| Behavior parity | **DEMONSTRATED**: `verify_target("cat")` 7/7 cases; 64 KiB arbitrary binary 65,536/65,536 bytes exact under `mb_ref`; 2,048-byte traced echo exact; full `make test` green (52 tests, independent Olmstead mirror 236 comparisons) |
| The four BOOT savings are safe | **DEMONSTRATED**: boot-end state differs in exactly two cells (`mem[59]`, `mem[89]`), neither ever read again (measured: zero write-phase touches of 89; identical write phase in both plans) |
| Post-handoff execution never reads low memory | **DEMONSTRATED for the traced horizon**: 840,730 steps / 2,048 echoed bytes — post-handoff `d` touches only 58,843..59,048 (0 touches below 7,311, 0 scratchpad touches); finite testing, not a proof |
| The 1,235-op boot is minimal | **NOT_DEMONSTRATED** — the four identified savings are exhausted; minimality is unproven |

## 2. Hypothesis and null

**H:** the 118-op k=18 gap is paid by the BOOT phase, not the write phase:
the write phase is k-invariant (5,964 ops, 68% `solve_sp` arithmetic per the
chain-sweeps cost split), so only the boot can fund the larger shift.
**H0:** the boot's 1,367 ops are all load-bearing; removing any breaks the
handoff. **H0 is REFUTED** for 132 of them (below); the remaining 1,235 are
asserted state at every stage but not proven minimal.

## 3. The four savings (BOOT steps 1..1434)

| # | original | compact | ops | why it is safe |
|---|---|---|---:|---|
| 1 | 515..523 pre-clear + 1286..1341 install `mem[89]=58328` (+729 odometer constant) | 515..523 → one `o`; 1286..1341 skipped | **−64** | the k=18 window (58,843..59,048) is one 729-aligned block; measured odometer picks `{92: 9, 91: 2, 90: 2, 89: 0}` in both plans |
| 2 | 51-op rotor walk on (58,59,60) | 27-op BFS shortest path | **−24** | same end state `a=59048, d=61`; residue `mem[59]` differs but is never read again |
| 3 | 271-op literal setup of scratchpad 48 (153..423) | 239-op rework installing `mem[53]=50`, `mem[54]=47` first | **−32** | staged asserts reproduce every scratch value; solve at 424 costs +2 |
| 4 | 23 ops at 630..652 installing `mem[93]=59048` | 8-op fuse `ojooooop` after the 1013 solve | **−12** | the 1013 solve already lands `d=94, a=59048` |
| | boot total | 1,367 → **1,235** | **−132** | |

Plan arithmetic: 7,331 − 132 = **7,199** ≤ 7,213. The write phase is
**unchanged**: 5,964 ops with the identical op string in both plans (S5:
identical odometer choices and scratchpad touch signatures).

## 4. Corrections to the handoff document (measured, not assumed)

- The saving is **−132**, not −134: the handed-over "was 1,369" boot count
  includes 2 ops the plan never emits; the reproducible baseline is 1,367
  (control C0 = 7,331 total).
- The boot-end state differs in **`mem[59]` (6563→1971) and `mem[89]`
  (58328→73)** — not "only mem[73]": that value (59046) was a mid-boot
  state at stage 6, not the boot end. `mem[73]` is identical at boot end.
- Measured odometer picks under the compact boot: `{92: 9, 91: 2, 90: 2}`
  (13 `+9` calls), `89` never chosen; the handoff's `{92: 15, 91: 5, 90: 2}`
  does not match either plan and is superseded by these numbers.
- Post-handoff low-memory safety is **measured** (S8), not inferred: 0 `d`
  touches below 7,311 over the traced horizon.

## 5. Independent verification (verify_k18.py)

Not a re-run of the handoff harness: a fresh driver with a control and its
own VM. Raw outputs: `out_verify_fast.txt` (S1–S8, 4 s) and
`out_verify_full.txt` (+S9).

| section | check | result |
|---|---|---|
| S1 | planner memory model vs real crazy-recurrence fill | exact on [0..1532] ∪ [9,381..59,048]; differs only on the image interior [1533..9,380] (7,784 cells, never read as `d` — proven by S8) |
| S2 | **control C0**: patched harness + original boot replay | **7,331 ops** (published frontier) — harness fidelity proven |
| S3 | in-repo `compact_boot.py` vs the handoff's scratch function | op-for-op identical, same final memory |
| S4 | boot-end memory diff (original vs compact) | exactly 2 cells: `mem[59]`, `mem[89]` |
| S5 | instrumented synthesis (odometer, scratchpad touches) | 7,199 total; write phase identical to the original-boot plan (same kcell/touch signatures, 5,964 = 5,964) |
| S6 | assembly + determinism | 7,690 cells; `end_c` 7,297; two independent rebuilds byte-identical; SHA-256 `0e14c807…` |
| S7 | canonical `compare_handoff` (keep-high) | AT_CELL both; 124/124; 0 mismatches |
| S8 | own-VM trace, 2,048-byte stream | echo exact; pre-handoff `d` only in [0..99] ∪ [58,843..59,048]; post-handoff `d` only in [58,843..59,048]; 0 low touches |
| S9 | `mb_ref` battery | 7/7 cases; 64 KiB binary 65,536/65,536 exact |

Two independent code paths produce the same artifact bytes: the evidence
harness (chain_synth + patched boot) and the canonical pipeline
(`tools/resynthesize.py` + `tools/compact_boot.py`) both give SHA-256
`0e14c807…`.

## 6. Integration (canonical pipeline)

- `tools/compact_boot.py`: canonical `build_compact_boot` (lazy-imported to
  avoid a module cycle).
- `tools/resynthesize.py`: `synthesize_preamble_ops` gains
  `restart_p1=0.60, restart_p2=0.75, boot="original"` — the previously
  hardcoded restart thresholds become parameters; the old behavior is the
  default, so the k=15 recipe (`boot="original"`, k=15, seed 47, pen 2,
  gap 9) still rebuilds the 7,972 bytes from git history.
- `tools/build_compact_cat.py`: `PLAN = {k: 18, seed: 9803, borrow_penalty: 1,
  direct_gap: 18, restart_p1: 0.80, restart_p2: 0.90, boot: "compact"}`.
- `artifacts/cat_compact.mal`: **replaced** by the 7,690-cell build (the
  7,972 bytes remain in git history; superseded, not deleted).
- `tests/test_compact_cat.py`: expectations updated (7,690 cells, k=18 plan,
  7,199 ops); the battery itself is unchanged (7 cases + 64 KiB stream +
  handoff 124/124).
- Gates: `python3 tools/build_compact_cat.py` → PASS (7 cases, 124/124,
  published); `--check` → byte-exact; `make test` → 52 tests OK, independent
  Olmstead mirror 236 comparisons PASS.

## 7. Reproduction

```bash
python3 docs/evidence/2026-10-25-compact-cat-k18/verify_k18.py         # S1-S8 (~4 s)
python3 docs/evidence/2026-10-25-compact-cat-k18/verify_k18.py --full  # + mb_ref battery
python3 tools/build_compact_cat.py --check                            # canonical rebuild
make test
```

## 8. Limits and next frontier

- All behavior gates are finite testing (7 cases, 64 KiB, 2,048-byte trace,
  236 mirror comparisons); no proof for every input.
- **Next frontier — smaller than 7,690** (k=19, budget 7,118): the compact
  boot plus the unchanged write phase totals 7,199, so k=19 needs **−81
  more**. The write phase is k-invariant and 68% `solve_sp` arithmetic
  (3,677 ops over 121 writes, 53 distinct `a_req` values —
  [`../2026-10-25-cat-chain-sweeps/REPORT.md`](../2026-10-25-cat-chain-sweeps/REPORT.md)
  §9), and window-tiling DP and chain sweeps are refuted there. The boot's
  1,235 ops are asserted-correct but not proven minimal. The next experiment
  is a cheaper `a_req` metric or a shorter boot, not another walk strategy.
