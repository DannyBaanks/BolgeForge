# BolgeForge roadmap

Status after the 2026-10-20 audit and repair. See [the audit](audits/2026-10-20-e2e/REPORT.md) and [repair evidence](repairs/2026-10-20/REPORT.md). Prior completion claims for rejected prototypes are withdrawn; raw historical evidence remains intact.

## Verified engineering

- [x] Quine m=281: 53,562 file bytes, exact self-reproduction and full deterministic synthesis demonstrated in the audit. Worldwide record: **RETIRED** (universal negative outside this evidence scope).
- [x] Strict loading and bounded execution, with separate failure codes for invalid sources, fuel exhaustion and invalid execution states.
- [x] Complete expected quine inventory checked without masked earlier failures.
- [x] Historical reference corpus tests and required compressed artifact checks.
- [x] Repair Digital Root and Adder handoff boundaries; verify candidates before publishing.
- [x] Explicit generation check for all four compressed targets, without modifying published artifacts.
- [x] Negative controls for the experimental programs previously misclassified as Classic.

## Open research

- [x] Certify a valid Classic streaming Cat: `cat_compressed.mal` and the historical Cat both stream 64 KiB binary input exactly and halt (`tests/test_cat_streaming.py`).
- [x] Construct a streaming Cat smaller than the verified 8,254-cell compressed Cat: `artifacts/cat_compact.mal`, **7,972 cells** (282 fewer), k=15 plan, handoff 124/124, exact-output battery including 64 KiB binary (`tools/build_compact_cat.py`; `tests/test_compact_cat.py`; evidence `docs/evidence/2026-10-24-compact-cat-k15/`). The 3,380-byte MicroCat remains an invalid, at-most-three-byte echo prototype; `candidate_cat_7893b.mal` remains broken (`d` 97 instead of 58,975).
- [x] Construct a streaming Cat smaller than 7,972 cells. **Achieved 2026-10-25: `artifacts/cat_compact.mal`, 7,690 cells** (−282), k=18 plan with the compact boot (1,235 ops, −132 in BOOT: the unused mem[89]=58328 odometer constant, a 27-op rotor BFS, the sp-48 setup rework, the mem[93] fuse), 7,199/7,213 preamble ops (margin 14), handoff 124/124, exact-output battery including 64 KiB binary and the independent mirror (`docs/evidence/2026-10-25-compact-cat-k18/`). The gap this closed was measured at +118 (7,331/7,213, 10,000 seeds); window-tiling DP and multi-target chain sweeps were refuted on the way (`docs/evidence/2026-10-24-window-dp-v0/REPORT.md`, `docs/evidence/2026-10-25-cat-chain-sweeps/REPORT.md`).
- [ ] Construct a streaming Cat smaller than 7,690 cells. k=19 budget 7,118 vs current floor 7,199 (boot 1,235 + k-invariant write phase 5,964): −81 more needed. The write phase is 68% `solve_sp` arithmetic (3,677 ops / 121 writes / 53 distinct `a_req` values); the boot's 1,235 ops are asserted-correct but not proven minimal; window-tiling DP, chain sweeps and the m1 `*jo` register transfer are refuted. Next lever: a cheaper `a_req` metric or a shorter boot, not another walk strategy (`docs/evidence/2026-10-25-compact-cat-k18/REPORT.md` §8).
- [x] Certify a loader-valid Classic Truth Machine and prove its productive branch: 90-byte reproduction, strict loader, `0` halts, `1` repeats the full VM state after 408 instructions with 17 bytes per cycle (`tools/prove_truth_machine.py`).
- [x] Generate a strict-valid behavior-preserving 90-byte variant: nine free-cell re-encodings, strict loader, `0` halts, `1` full-state cycle 408/17; `tools/synthesize_truth_machine_variant.py`; evidence `docs/evidence/2026-10-22-truth-machine-variant/`. This is a derivative variant, not independent synthesis.
- [x] Synthesize an equivalent Truth Machine independently/from scratch inside BolgeForge. The 90-byte reference and its variant are documented reproductions/derivatives (CC BY-SA 4.0). First attack (2026-10-24): exhaustive prefix search of decoded-op programs to depth 6 (295,584 candidates, exact engine validated bit-exact against the prover on the reference) — **refuted**, 0 survivors; next route: installer-based kernel (`docs/evidence/2026-10-24-truth-machine-independent/REPORT.md`). **Closed 2026-10-25**: independent 120-cell program with its own kernel geometry (`78/79/80`, window `112..117`), own entry/branch and own runtime installer (installs `63` at cell 116 via `a=0 → 29533 → 63`); strict loader ACCEPT (0 invalid cells), `0` → HALT step 27 / `30`, `1` → full-state cycle 408 with 17 all-`31` outputs per cycle, `mb_ref` agrees at 200k and 1M steps. `tools/prove_truth_machine.py` verdict `DEMONSTRATED`; `docs/evidence/2026-10-25-truth-machine-v5/` (`build_v5.py` regenerates the artifact; SHA-256 `7b74ec811d9f44d6…`). Loader obstruction proven by enumeration: loader-valid positions of a value never differ by 2 or 4, so one window cell always requires runtime installation.
- [x] Certify a loader-valid FizzBuzz that runs with empty stdin: preserved angel_p_57 reference, 413 bytes, 100 lines, strict HALT (`tests/test_fizzbuzz_reference.py`).
- [ ] Zero-read FizzBuzz and divisibility computed inside the VM remain open research and are not claimed.
- [x] Q/C selector: retired as a published claim. The M3 candidate fails strict loading; the contract's CAT payload echo is open research if pursued.
- [ ] Extend compression and arithmetic coverage beyond the documented finite vectors. Adder operands remain limited to 0..999 by the historical program's contract.
- [ ] Investigate smaller feasible quine parameters. Record failures and do not label m=278 achieved without a valid generated artifact and exact execution evidence.

Fibonacci generation, arbitrary parametric synthesis and other novel programs remain ideas. They have no completion or primacy label. Algebraic lemmas and synthesis strategies are research tools; each complete program still needs loading, execution, negative controls and preserved evidence.
