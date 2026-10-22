# Truth Machine variant synthesis — 2026-10-22

Status: **VARIANT_DEMONSTRATED**. This is a behavior-preserving derivative of
the 90-byte CC BY-SA 4.0 reference, not an independent from-scratch synthesis.
Independent architecture synthesis remains `OPEN / NOT_DEMONSTRATED`.

## Scope

The reference is `artifacts/truth_machine_classic_90b.mal` (90 bytes, SHA-256
`1e34e2afd1fc645dadac1f1aac0fe2348ff469878cc3da396a6a1e7bad2a4417`).
The generator traces it for inputs `0` and `1`, finds cells that are never read
or written, re-encodes those cells with different valid Classic opcodes, and
verifies the result. No read or branch cell is changed.

This establishes that a second strict-valid, behaviorally equivalent 90-byte
source exists. It does not establish a new algorithm, a smaller Truth Machine,
or historical primacy.

## Method

1. Load the reference under the strict Classic rules (`ji*p</vo` only).
2. Execute both required branches for 3,000 instructions and record every
   `c`/`d` read and every memory write.
3. Select cells outside the union of reads and writes.
4. Replace each selected opcode with the next opcode in `OPS` that round-trips
   through `XLAT1` at that address.
5. Verify the candidate with the strict loader, the local cycle checker, and
   the canonical prover.

## Result

- Variant: `artifacts/truth_machine_variant_90b.mal`
- Size: **90 bytes**
- SHA-256: `08691d13d55141f9458df4ac43f802acc7e72f405a2459c302b40f727bf53f09`
- Strict loader: **ACCEPT**
- Input `0`: `HALT` at instruction 38, output `30` (one `0`)
- Input `1`: full-state cycle, period **408** instructions, **17** output bytes
  per cycle, all `31` (`1`); 58 output bytes observed through instruction 1408
- Full-state cycle SHA-256: `e2005dd6e9799880f70a9c1d9c042db1674491eed25fdb94c7e1906fa0f7539a`
- `mb_ref` input `0`: exit 0, stdout `30`
- `mb_ref` input `1` with budget 1408: exit 2 (`MAX_STEPS`), 58 bytes, all `31`

### Free cells and changes

| Cell | Old byte | Old op | New byte | New op |
|---:|---:|---|---:|---|
| 38 | 124 | `o` | 96 | `j` |
| 39 | 123 | `o` | 95 | `j` |
| 40 | 122 | `o` | 94 | `j` |
| 70 | 92 | `o` | 64 | `j` |
| 71 | 91 | `o` | 63 | `j` |
| 72 | 90 | `o` | 62 | `j` |
| 85 | 77 | `o` | 49 | `j` |
| 86 | 76 | `o` | 48 | `j` |
| 87 | 75 | `o` | 47 | `j` |

The nine cells are never read or written in the traced branches. The variant
therefore preserves the observed behavior without solving a new branch target.

### Negative controls

Four read cells were re-encoded with the same deterministic rule and stayed
strict-loader-valid, but each failed the specification: cells `0`, `37`, `41`
and `73` produced `INVALID_EXECUTION` on at least one branch or changed the
`0` branch from `HALT` to `INVALID_EXECUTION`. Their recorded verdicts are
`NOT_DEMONSTRATED`. This control distinguishes the never-read cells from cells
whose opcode is behaviorally live.

## Commands

```bash
python3 tools/synthesize_truth_machine_variant.py
python3 tools/prove_truth_machine.py artifacts/truth_machine_variant_90b.mal --json
printf '0' | ./mb_ref artifacts/truth_machine_variant_90b.mal 10000
printf '1' | ./mb_ref artifacts/truth_machine_variant_90b.mal 1408
```

The generator exits 0. The prover exits 0 with `verdict: DEMONSTRATED`.
`mb_ref` exits 0 on `0` and 2 (budget exhausted) on `1`; the latter is the
expected non-halting result for the productive branch.

## Claims

| Claim | Status | Evidence |
|---|---|---|
| A strict-valid 90-byte variant of the reference exists | **DEMONSTRATED** | strict loader ACCEPT; `mb_ref`; `tools/prove_truth_machine.py` |
| The variant preserves the tested Truth Machine behavior | **DEMONSTRATED** for inputs `0` and `1` | HALT/`0`; full-state cycle 408/17 |
| The variant is an independent, from-scratch Truth Machine | **NOT_DEMONSTRATED** | It is derived from the reference by free-cell re-encoding |
| The variant is minimal or historically novel | **NOT_DEMONSTRATED** | No minimality or primacy proof |
| A new algorithm or architecture was synthesized | **NOT_DEMONSTRATED** | No new branch/read/write structure |

## Not demonstrated

- Independent synthesis without the CC BY-SA 4.0 reference.
- Minimality below 90 bytes.
- Historical primacy or a world record.
- Behavior outside the Truth Machine specification (inputs other than `0`/`1`).
- Any claim that the variant’s cycle proof extends to a different program.

## Reproduction and hashes

`report.json` contains the full machine-readable trace summary, the exact
change list, the prover payload, and both `mb_ref` results. `SHA256SUMS.txt`
covers the published artifact and the report. The generated `candidate.mal`
is byte-identical to the published artifact.

The reference and this variant retain CC BY-SA 4.0 attribution; see
`docs/provenance/truth_machine_90b.json`.
