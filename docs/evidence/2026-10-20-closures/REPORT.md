# Closure evidence — 2026-10-20

Environment: Linux (Ubuntu 24.04), Python 3.12.3, `oracle/mb_ref.c` built with
`make`. Exact commands in `commands.txt`; SHA-256 sums in `SHA256SUMS.txt`.

## Truth Machine

`artifacts/truth_machine_classic_90b.mal` (90 bytes, SHA-256
`1e34e2afd1fc645dadac1f1aac0fe2348ff469878cc3da396a6a1e7bad2a4417`,
provenance `docs/provenance/truth_machine_90b.json`).

- Input `0`: HALT after 38 instructions; output `30` (one `0` byte).
- Input `1`: full machine state (a, c, d and all 59,049 memory cells) repeats
  from instruction 1000 to instruction 1408. Period 408 instructions; 17 output
  bytes per cycle; every output byte is `31` (`1`).
- Consequence: deterministic repetition of the complete state with positive
  emission per period proves an infinite `1` stream. This is not inferred from
  a finite output prefix.
- Raw report: `truth_machine_proof.json`.
- Cross-check: `printf '1' | ./mb_ref ... 1408` emits exactly 58 `1` bytes and
  exits 2 (budget exhausted), matching the prover.

## Streaming Cat

`artifacts/cat_compressed.mal` (8,254 cells) and
`reference/malbolge_org/cat.mal` (9,503 bytes) were fed the 65,536-byte binary
`payload.bin` (SHA-256 `011e7766…`). Both returned exit 0, HALT, and byte-exact
output. Raw report: `cat_streaming.json`.

## FizzBuzz

`docs/audits/2026-10-20-e2e/angel_fizzbuzz_converted.mal` (3,590 bytes,
preserved angel_p_57 conversion) was run with empty stdin. Result: exit 0,
413 bytes, 100 lines, exact canonical FizzBuzz text, SHA-256
`f039dc22…`. The program performs 109 EOF reads; zero-read behaviour is not
claimed. Raw report: `fizzbuzz_reference.json`.

## Tests

`python3 -m unittest tests.test_truth_machine_strict tests.test_cat_streaming
tests.test_fizzbuzz_reference -v` — 12 tests, all pass (1.671 s in the recorded
run). The same tests are part of `tests/` and therefore of `make test`.

## Scope

These results certify the listed artifacts and vectors. They do not establish
worldwide quine supremacy, historical primacy, autonomous synthesis of the
Truth Machine, zero-read FizzBuzz, or a Q/C selector. Those claims are RETIRED
or OPEN in `docs/CLAIMS.md`.
