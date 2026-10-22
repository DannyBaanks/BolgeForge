# Square 0..9 — LMAO oracle experiment

Status: **ORACLE-DERIVED EXPERIMENT**, not a BolgeForge synthesis.

This directory preserves the verified `square(0..9)` result produced with
LMAO v0.6.0. It is intentionally kept outside `artifacts/` and outside the
certified BolgeForge claims because its source is derived from a GPL-3 LMAO
example. The project rule for new work is:

- **LMAO is the oracle/reference.**
- **BolgeForge is the synthesizer.**

No claim in this directory says that BolgeForge generated the program.

## Artifact

| File | Bytes | SHA-256 |
|---|---:|---|
| `square.mal` | 42,189 | `391b9641691f310170ecb64daefd61fce2621adc640dba10e3149e4f286bae26` |
| `square.hell` | 17,475 | `70edc01d64413e837fb431ef2cf87cf9599c00ba94eb101f5f67248f8970dd07` |

`square.hell` is LMAO's `example_digital_root.hell` with its first
`print_result` label renamed to `old_print_result` and a new `.DATA` dispatch
block appended. For the single decimal digits `0..9`, the dispatch selects the
corresponding square.

The LMAO checkout used was commit `3ea747e16b45ea7627018b291409b12c1f9ca3dc`
(v0.6.0). The LMAO source header is GPL-3-or-later; the derived source and
artifact retain that provenance.

## Verified behavior

`mb_ref` (Olmstead Classic Malbolge) with one digit, with or without a trailing
newline:

```text
input  output
0      0
1      1
2      4
3      9
4      16
5      25
6      36
7      49
8      64
9      81
```

`tools/prove_truth_machine.loader_cells` accepts the artifact and expands it to
59,049 cells.

The inherited digital-root pipeline means multi-digit input is reduced before
the dispatch: for example, `12` produces `9` (digital root `3`, squared). That is
outside the single-digit `0..9` scope and is not claimed as general arithmetic.

## Reproduce

```bash
cd "$(git rev-parse --show-toplevel)"
make mb_ref
python3 experiments/square_0_9_lmao_oracle/verify_square.py
```

The verifier checks the source/artifact hashes, the strict loader, and all ten
single-digit vectors with and without a trailing newline.

## Limits

- Single decimal digit `0..9` only; not `product(a,b)`.
- Not a BolgeForge-native synthesis and not a certified MIT-core artifact.
- The 100-case product lookup table was tested separately and failed with
  `Free space exceeded (Add Malbolge command)` at cell 57,637 (59,049-cell
  Classic limit). Product remains open.
- No new historical/primacy claim follows from this experiment.
