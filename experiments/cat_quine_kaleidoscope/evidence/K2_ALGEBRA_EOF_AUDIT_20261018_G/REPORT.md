# K2 algebra audit G — republished, path-normalised re-run of the same suite

Date: 2026-10-18 · Stage: `K2_ALGEBRA_EOF_AUDIT_20261018_G`
Suite: `experiments/cat_quine_kaleidoscope/tools/test_k2_algebra.py` (10 tests)
Previous stages in this family: `..._A`, `..._B`, `..._C`, `..._D` (Sol, OpenCode
"Malbolge quine" session, GPT-6.1) and `..._F` (this session, superseded — see §4).

## 1. Why this stage exists

Stages A–D are byte-good evidence but cannot be published: each `results.json`
records the workstation location of the run (`"cwd"` and the `-I <abs ROOT>` of
the shim compile command), and the repo-engine pre-commit gate classifies a
private path in a `.json` as `LOCAL_PATH_001` **CRITICAL**. The gate blocked the
commit; no hook was bypassed and nothing was pushed.

The fix belongs in the recorder, not in the findings. `test_k2_algebra.py` now
normalises every recorded path through `rel()`:

- absolute repo paths → repo-relative (`experiments/cat_quine_kaleidoscope/work/…`)
- absolute paths outside the repo (interpreter, `cc`, the per-run temporary
  build) → `<outside-repo>/<basename>`
- relative argv tokens (flags, the `--evidence` argument) → unchanged
- `"cwd": "."` — the recorded commands are runnable verbatim from the repo root

A `path_recording` key states this inside `results.json` so a reader does not
have to trust the prose.

## 2. What did NOT change

Re-running the same suite with the normalised recorder reproduces stage D
exactly. Comparison performed with `json.load` on both `results.json` files:

| Field | D vs G |
|---|---|
| `tests`, `exit_status` | equal (10 tests, exit 0) |
| `c_oracle_library_sha256` | equal `fc93e7af…` |
| `searches.raw` / `searches.stored` (stats + best) | equal; best stored `[24, 19, 7263, 46196, 55430, 49355, 45319, 25649, 25892]` |
| `vm_runs[*].summary` | equal: Q `steps=62239932 halt=v prints=53562 out_bytes=53562 anomalies=0`, C `steps=25533 halt=v prints=0 out_bytes=0 anomalies=0` |
| `Q_stdin.bin`, `Q_stdout.bin`, `C_stdin.bin`, `C_stdout.bin` | **byte-identical** (`cmp`), `Q_stdout.bin` sha256 `7cab1285…` |
| `inputs_sha256` key set | equal |
| `inputs_sha256` values | differ in exactly one entry: the patched `tools/test_k2_algebra.py` itself (`aa7d3e9a…` → `bcf58df8…`) |

So the path normalisation touched only the machine-location metadata. Every
algebraic and VM claim carried by A–D stands as recorded, and now has a
publishable stage.

Headline content of the suite, unchanged from D and restated for readers who
only see this stage:

- EOF is `59048` = `88888₉`, **not** `22222₉ = 14762`; the corrected digit
  reading is what makes the gate witnesses meaningful.
- Operator orientation `op(ctrl, cell) = O[cell_digit][ctrl_digit]` per base-9
  digit: 354,294 full-word C comparisons agree with the Python table, and the
  swapped-order control differs (`op(81,29524) != op(29524,81)`) — trap T24.
- Full initial-memory parity for both artifacts: 59,049 cells match the C pad;
  the swapped pad mismatches 4,666 cells (negative control).
- Reach cache: 26,944 witnessed values, closed under `R` and `P(33..126)`.
- 40 (`k2_gate`) + 30 (`k2_branch`) printed gate witnesses re-verified with the
  real EOF class, each checked over 257 inputs against the compiled oracle.
- Rearm controls `(29524, 59048, 0)`: for **all** 59,049 cell values, the
  three-fold `op` cascade lands on `29524`; each control is `rot`-fixed.
  `R4 = op(·, 29524)` is an involution on bytes and EOF.
- Selector unchanged: `Q` reaches loop entry (`c=25976, d=26409, a=26407, ip=1`,
  0 prints) and the compiled oracle echoes the 53,562-byte source exactly;
  `C` halts at `Z=36` after 25,533 steps with **0 bytes out**.

## 3. What this stage still does not show

Nothing here is a K2 program. `not_demonstrated` in `results.json` is carried
over verbatim: executable K2, CAT payload echo, rearm routing, a stable
self-encrypting echo loop, two-engine parity. In particular stage D's planned
next step — "realise one stored-byte witness with actual `d` routing" — is
falsified, not merely unimplemented: see
`experiments/cat_quine_kaleidoscope/evidence/K2_PSI_ROUTE_20261018_E/REPORT.md`
§1. Only `(4,8)` of the 81 `(store_row, read_ctrl)` pairs is injective on the
byte digits, and the required inverse is absent from the verified-complete
207-map row-composition closure. The stored-byte witnesses in `searches.stored`
are therefore not candidates awaiting routing.

## 4. Superseded stage F

The first run after the recorder fix (`..._F`) normalised non-path argv tokens
too, so its `command` array reads `<outside-repo>/-B`, `<outside-repo>/--evidence`.
That is leak-free but misleading metadata. `F` is left on disk untouched —
evidence paths are never reused and no recorded hash is rewritten — and `G`
supersedes it with the corrected `rel()`.

## 5. Stages A–D remain on disk, uncommitted

A–D are Sol's raw captures with the original absolute-path metadata and their
own `hashes.json`. They are preserved as recorded, not edited after the fact,
and not committed, because committing them would publish the workstation path.
Their substance is now carried by `G` (byte-identical VM captures) and the
claims are also re-derived in `K2_PSI_ROUTE_20261018_E`.

## 6. Reproduction

```bash
cd <repo root>
python3 -B experiments/cat_quine_kaleidoscope/tools/test_k2_algebra.py \
  --evidence experiments/cat_quine_kaleidoscope/evidence/<NEW_DIR>
```

Requires `cc`. The evidence directory must not exist; files are written with
`open(..., "xb")`, so no existing report or artifact is overwritten.
