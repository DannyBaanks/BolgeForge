# Claims ledger — BolgeForge

Status after the 2026-10-20 audit and closure pass. The audit report
(`docs/audits/2026-10-20-e2e/REPORT.md`) is historical evidence and is not
rewritten. This ledger maps every published claim to a terminal status:

- **DEMONSTRATED** — reproduced here with executable evidence.
- **REFUTED** — contradicted by the audit or by a strict-loader control.
- **RETIRED** — withdrawn from publication. Neither asserted nor denied; used
  for universal/historical negatives that this repository cannot establish.
- **OPEN** — explicitly unclaimed active research.

Every published claim has one of the four terminal statuses above; the
audit-result column preserves historical `NOT_DEMONSTRATED` findings.

| Claim | Audit result | Terminal status | Evidence |
|---|---|---|---|
| Quine m=281, 53,562 bytes, exact self-reproduction | DEMONSTRATED | **DEMONSTRATED** | `tools/test_quines.py`, audit `synthesis_m281_result.json` |
| Quine m=281 is the world record | NOT_DEMONSTRATED | **RETIRED** (universal negative) | — |
| Five committed quines self-reproduce under strict loading | DEMONSTRATED | **DEMONSTRATED** | `tools/test_quines.py` |
| Eight historical reference programs behave as documented | DEMONSTRATED | **DEMONSTRATED** | `test_corpus.py` |
| Four compressed benchmarks match the documented vectors | DEMONSTRATED | **DEMONSTRATED** | `tools/test_compressed.py` |
| Digital Root and Adder regenerate byte-identically | PARCIAL → repaired | **DEMONSTRATED** | `make test-rebuild`, `docs/repairs/2026-10-20/checks.json` |
| MicroCat is a general streaming Cat | REFUTED | **REFUTED** as Classic artifact | `runs/models.json`; `ABCD` → `ABC` |
| Classic streaming Cat exists | DEMONSTRATED via `cat_compressed.mal` and the historical Cat | **DEMONSTRATED** | `tests/test_cat_streaming.py`; `docs/evidence/2026-10-20-closures/cat_streaming.json` (64 KiB binary, exact, HALT) |
| A streaming Cat smaller than 8,254 cells exists | — | **DEMONSTRATED** | `artifacts/cat_compact.mal`: **7,596 cells** (564 fewer, 6.8%; 1,692 fewer than the 9,382-cell reference), SHA-256 `80b9dca9…`, exact-output battery including 64 KiB binary, handoff 124/124 (`tests/test_compact_cat.py`; `tools/build_compact_cat.py`; evidence `docs/evidence/2026-10-25-cat-k19-frontier/`; first demonstrated at 7,972 cells on 2026-10-24, superseded by 7,596 on 2026-10-25) |
| A streaming Cat smaller than 7,972 cells exists | — | **DEMONSTRATED** | `artifacts/cat_compact.mal`: **7,596 cells** (282 fewer), k=19 plan with the compact boot (1,196 ops, −132 in BOOT: the unused mem[89]=58328 odometer constant, a 27-op rotor BFS, the sp-48 setup rework, the mem[93] fuse), joint beam search (beam 128) on write order + spindle assignment saves 108 ops (write 5,883 vs 5,991), NOP compression (24 ops), 7,056/7,119 preamble ops (margin 63), handoff 124/124, exact-output battery + 64 KiB binary + independent mirror; SHA-256 `80b9dca9…` (`docs/evidence/2026-10-25-cat-k19-frontier/`). History: the gap was measured at +118 (7,331/7,213, 10,000 seeds); window-tiling DP, chain sweeps, m1 `*jo` transfer, and A* boot optimization all refuted as paths to the gap; the breakthrough was the k=19 joint search + A* boot (−172 ops combined) — `docs/evidence/2026-10-25-cat-k19-frontier/REPORT.md` §10 |
| A streaming Cat smaller than 7,596 cells exists | — | **OPEN** | k=20 budget 7,025 vs current floor 7,056 (boot 1,196 + write 5,883): −31 more needed. The write phase is k-invariant and 68% `solve_sp` arithmetic (3,337 ops over 121 writes, 53 distinct `a_req`); the boot's 1,196 ops are asserted-correct but not proven minimal; A* segment re-synthesis and joint beam search are refuted as paths to the gap — `docs/evidence/2026-10-25-cat-k19-frontier/REPORT.md` §10 |
| Truth Machine is a Classic program | REFUTED for the 103-byte artifact | **DEMONSTRATED** by the 90-byte strict-valid reproduction | `artifacts/truth_machine_classic_90b.mal`; `tools/prove_truth_machine.py`; `tests/test_truth_machine_strict.py` |
| Truth Machine `0` branch prints one `0` and halts | — | **DEMONSTRATED** | HALT at instruction 38, output `30` |
| Truth Machine `1` branch emits `1` forever | NOT_DEMONSTRATED for the old artifact | **DEMONSTRATED** by full-state cycle | Period 408 instructions; 17 output bytes per cycle; state SHA-256 `6962734d54aa4f33…`; evidence `truth_machine_proof.json` |
| Behavior-preserving 90-byte Truth Machine variant exists | — | **DEMONSTRATED** (derivative variant) | 9 free-cell re-encodings; SHA-256 `08691d13d55141f9458df4ac43f802acc7e72f405a2459c302b40f727bf53f09`; strict `mb_ref`; `tools/prove_truth_machine.py`; `docs/evidence/2026-10-22-truth-machine-variant/REPORT.md` |
| The variant is an independent from-scratch synthesis | — | **NOT_DEMONSTRATED** | Derived from the CC BY-SA 4.0 90-byte reference; independent synthesis remains OPEN |
| An independent from-scratch Truth Machine passes the strict loader | — | **DEMONSTRATED** (2026-10-25) | `docs/evidence/2026-10-25-truth-machine-v5/tm_independent_v5.mal`: 120 cells, SHA-256 `7b74ec811d9f44d6…`, loader ACCEPT (0 invalid cells), `0` → HALT step 27 output `30`, `1` → full-state cycle period 408, 17 outputs/cycle, all `0x31` (`tools/prove_truth_machine.py`, `state_sha256 c36f15dc…`); `oracle/mb_ref` (recompiled 2026-10-25) `0` rc=0 `30`, `1` rc=2 all-`31` at 200k and 1M steps. Own kernel geometry (`78/79/80`, window `112..117`), own entry/branch/installer; only the already-decoded kernel *mechanism* is shared |
| The v4 candidate (2026-10-24) synthesised a valid strict-loader Truth Machine | — | **REFUTED** | Worked in the exact engine but violated the strict loader in 35 cells (`LOADER_REJECT: cell 47 decodes to '{'`); kept as negative evidence in `docs/evidence/2026-10-24-truth-machine-independent/` |
| One loader-invalid window cell is unavoidable for this kernel family | — | **DEMONSTRATED** (enumeration) | Loader-valid positions of any value never differ by 2 or 4 (valid XLAT1 op indices `{6,7,29,35,48,65,66,84}`); the kernel window requires R1 at `dG` and `dG+2` (or `dG-4`), so runtime installation is mandatory. `docs/evidence/2026-10-25-truth-machine-v5/REPORT.md` |
| Truth Machine historical primacy | NOT_DEMONSTRATED | **RETIRED** | — |
| Loader-valid FizzBuzz exists | REFUTED for the 4,517-byte artifact | **DEMONSTRATED** via the preserved angel_p_57 conversion | Empty stdin; 413 bytes; 100 exact lines; HALT; SHA-256 `f039dc221ad122dd…`; `tests/test_fizzbuzz_reference.py` |
| FizzBuzz with zero stdin reads | NOT_DEMONSTRATED | **RETIRED** | Reference performs 109 EOF reads |
| FizzBuzz divisibility computed inside the VM / historical primacy | NOT_DEMONSTRATED | **RETIRED** | Reference emits fixed text recipes |
| Valid Q/C selector (Q → source, C → payload echo) | REFUTED for the M3 candidate | **RETIRED** as published claim; CAT payload echo **OPEN** | M3 candidate rejected by strict loader; `experiments/cat_quine_kaleidoscope/` |
| EOF defect in the included historical `cat.mal` | REFUTED | **REFUTED** | Audit telemetry: clean HALT, no `0x88` |
| Adder accepts operands above 999 | out of contract | **REFUTED** as a compression defect (inputs outside the author's `0..999` domain) | `adder_domain.json` |
| “24 theorems” / algebra certifies complete programs | NOT_DEMONSTRATED | **RETIRED** | Identities are limited to the audited algebra checks |

## Reproduction

```bash
make
make test
python3 tools/prove_truth_machine.py artifacts/truth_machine_classic_90b.mal --json
python3 -m unittest tests.test_truth_machine_strict tests.test_cat_streaming tests.test_fizzbuzz_reference -v
python3 tools/verify_handoff_state.py --reference reference/malbolge_org/cat.mal \
  --reference-cell 9067 --candidate artifacts/candidate_cat_7893b.mal --delta 1598
```

Raw closure evidence, commands and hashes:
`docs/evidence/2026-10-20-closures/`.
