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
- [ ] Construct a streaming Cat smaller than 7,972 cells. Measured frontier (2026-10-24, later): the best k=18 plan is 7,331 preamble operations against a 7,213 budget (+118; 10,000 seeds); k=16 is 7,612/7,400 and k=17 7,694/7,306. The 7,210-operation k=18 plan that omitted cells 58,844/59,046 is invalid: both cells are live (the artifact dies at 58,844; patching both gives 124/124, one gives 123/124). Details: `docs/evidence/2026-10-24-compact-cat-k15/k18_attack/ERRATA.md`.
- [x] Certify a loader-valid Classic Truth Machine and prove its productive branch: 90-byte reproduction, strict loader, `0` halts, `1` repeats the full VM state after 408 instructions with 17 bytes per cycle (`tools/prove_truth_machine.py`).
- [x] Generate a strict-valid behavior-preserving 90-byte variant: nine free-cell re-encodings, strict loader, `0` halts, `1` full-state cycle 408/17; `tools/synthesize_truth_machine_variant.py`; evidence `docs/evidence/2026-10-22-truth-machine-variant/`. This is a derivative variant, not independent synthesis.
- [ ] Synthesize an equivalent Truth Machine independently/from scratch inside BolgeForge. The 90-byte reference and its variant are documented reproductions/derivatives (CC BY-SA 4.0).
- [x] Certify a loader-valid FizzBuzz that runs with empty stdin: preserved angel_p_57 reference, 413 bytes, 100 lines, strict HALT (`tests/test_fizzbuzz_reference.py`).
- [ ] Zero-read FizzBuzz and divisibility computed inside the VM remain open research and are not claimed.
- [x] Q/C selector: retired as a published claim. The M3 candidate fails strict loading; the contract's CAT payload echo is open research if pursued.
- [ ] Extend compression and arithmetic coverage beyond the documented finite vectors. Adder operands remain limited to 0..999 by the historical program's contract.
- [ ] Investigate smaller feasible quine parameters. Record failures and do not label m=278 achieved without a valid generated artifact and exact execution evidence.

Fibonacci generation, arbitrary parametric synthesis and other novel programs remain ideas. They have no completion or primacy label. Algebraic lemmas and synthesis strategies are research tools; each complete program still needs loading, execution, negative controls and preserved evidence.
