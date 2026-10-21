# Repair and closure report — 2026-10-20

Baseline audited: `2fe8e8091dae71188ce4d98b8e10199a8a8b783f`.
Audit: `docs/audits/2026-10-20-e2e/REPORT.md` (historical evidence, unchanged).
This report records the repairs applied on top of the audit and the later
closure pass. Raw command output was captured locally (`checks.json`, `*.log`,
`*.stdout`, `*.stderr`); six logs containing absolute local paths are excluded
from Git and public sanitized copies are in `public/` (see Privacy below).
Closure evidence is in `docs/evidence/2026-10-20-closures/`.

## Repairs

- `oracle/mb_ref.c`: strict loader validation against the eight Classic
  instructions at each load address; reject sources shorter than two cells,
  invalid bytes, oversized inputs and non-numeric step budgets; report a
  nonprintable program counter instead of inventing a NOP; reject undefined
  encryption words; exit codes: 0 HALT, 1 source/argument error, 2 budget
  exhausted, 3 stall/undefined encryption, 4 I/O error.
- `Makefile`: `test` now requires the oracle regressions, corpus, compressed
  vectors, every committed quine and the independent Olmstead mirror. A missing
  or failing artifact fails the suite; earlier failures are not masked.
- `tools/test_compressed.py`: missing artifacts are failures, not silent passes.
- `tools/resynthesize.py`: Digital Root and Adder rebuilt with the actual linear
  handoff boundaries (31,802 and 55,802); candidates are validated before
  publication and `--check` never changes committed artifacts.
- `README.md`, `docs/ROADMAP.md`: withdrawn claims, explicit scope and current
  statuses; every current claim has a terminal status in `docs/CLAIMS.md`.
  Historical audit findings and experiment artifacts keep their original
  `NOT_DEMONSTRATED` labels as evidence.
- `experiments/cat_quine_kaleidoscope/CORRECTION_20261020.md`: the frozen M0/M3
  contract used a permissive VM; the selector candidate is rejected by the
  strict loader. Historical evidence remains untouched.

## Closure pass (new in this report)

- **Truth Machine**: `artifacts/truth_machine_classic_90b.mal` (strict-valid,
  90 bytes, reproduced with provenance). Input `0` halts in 38 instructions and
  prints `0`; input `1` repeats the full VM state (a, c, d and all 59,049
  memory cells) from instruction 1000 to 1408, emitting 17 bytes per 408-step
  cycle. This proves an infinite `1` stream. Tool:
  `tools/prove_truth_machine.py`; tests: `tests/test_truth_machine_strict.py`.
- **Classic streaming Cat**: `artifacts/cat_compressed.mal` and
  `reference/malbolge_org/cat.mal` stream a 65,536-byte binary payload exactly
  and halt. Tests: `tests/test_cat_streaming.py`.
- **Loader-valid FizzBuzz**: the preserved angel_p_57 conversion runs with empty
  stdin, emits 413 bytes / 100 exact lines and halts. It performs 109 EOF reads;
  zero-read behaviour and historical primacy are retired, not claimed. Tests:
  `tests/test_fizzbuzz_reference.py`.

## Current checks

From `checks.json` (2026-10-20T21:59:52Z, Linux, Python 3.12.3):

| Check | Result |
|---|---|
| `make test` | exit 0, 19.568 s |
| Strict-loader negative controls | `INVALID_OPCODE`, `TOO_SHORT`, invalid budget, excess arguments rejected |
| Old experimental artifacts | correctly rejected (`truth_machine.mal`, `fizzbuzz.mal`, `microcat.mal`) |
| `make test-rebuild` | four compressed artifacts PASS in the preserved log (cat 16 s, digital_root 32 s, adder 72 s, 99_bottles 218 s); a rerun in the closure session reached 99_bottles before a 300 s tool timeout, not a failure |
| Independent Olmstead mirror | 231 exact-output comparisons |

Additional closure tests (2026-10-20): 12 tests pass in 1.671 s
(`test_truth_machine_strict`, `test_cat_streaming`, `test_fizzbuzz_reference`).

## Privacy

Six raw logs contained absolute local paths (`legacy-tm.stderr`,
`oracle-before.log`, `independent-invalid-input-attempt.log`,
`verifiers-before.log`, `trace-before.log`, `legacy-fizzbuzz.stdout`). The
originals stay local and are excluded by `.gitignore`; `public/` contains copies
that replace only the repository prefix with `<REPO>`. `public/redaction.json`
records the raw and public SHA-256 values. Hashes in `checks.json` refer to the
raw originals, not to the sanitized copies.

## Remaining limits

- Worldwide quine supremacy, historical primacy and similar universal or
  historical negatives are **RETIRED**, not demonstrated.
- A streaming Cat smaller than 8,254 cells remains open research; MicroCat is
  invalid and `candidate_cat_7893b.mal` stalls at step 7,372.
- Zero-read FizzBuzz and divisibility computed inside the VM remain open.
- The Q/C selector is retired as a published claim; the contract's CAT payload
  echo remains open.
- The Truth Machine is a documented reproduction, not an autonomous BolgeForge
  synthesis. Its source is CC BY-SA 4.0
  (`docs/provenance/truth_machine_90b.json`).
