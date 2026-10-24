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
| A streaming Cat smaller than 8,254 cells exists | — | **OPEN** | `candidate_cat_7893b.mal` is loader-valid but fails at step 7,372 (`INVALID_ENCRYPTION`); it installs 0 of the reference's 124 handoff variables and enters the loop with `d = 97` instead of `57,377` (`tools/verify_handoff_state.py`; `docs/evidence/2026-10-23-compact-cat-diagnosis/`) |
| Truth Machine is a Classic program | REFUTED for the 103-byte artifact | **DEMONSTRATED** by the 90-byte strict-valid reproduction | `artifacts/truth_machine_classic_90b.mal`; `tools/prove_truth_machine.py`; `tests/test_truth_machine_strict.py` |
| Truth Machine `0` branch prints one `0` and halts | — | **DEMONSTRATED** | HALT at instruction 38, output `30` |
| Truth Machine `1` branch emits `1` forever | NOT_DEMONSTRATED for the old artifact | **DEMONSTRATED** by full-state cycle | Period 408 instructions; 17 output bytes per cycle; state SHA-256 `6962734d54aa4f33…`; evidence `truth_machine_proof.json` |
| Behavior-preserving 90-byte Truth Machine variant exists | — | **DEMONSTRATED** (derivative variant) | 9 free-cell re-encodings; SHA-256 `08691d13d55141f9458df4ac43f802acc7e72f405a2459c302b40f727bf53f09`; strict `mb_ref`; `tools/prove_truth_machine.py`; `docs/evidence/2026-10-22-truth-machine-variant/REPORT.md` |
| The variant is an independent from-scratch synthesis | — | **NOT_DEMONSTRATED** | Derived from the CC BY-SA 4.0 90-byte reference; independent synthesis remains OPEN |
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
