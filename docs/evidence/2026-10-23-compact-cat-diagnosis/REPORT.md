# Compact-cat pilot: the preamble never installs the variable table (0 of 124)

Date: 2026-10-23 · Program: `artifacts/candidate_cat_7893b.mal` (7,893 B / 7,784 cells, local
scratch, regenerable) · Gate: `tools/verify_handoff_state.py` · Raw numbers:
[`measurements.json`](measurements.json), [`handoff_state.json`](handoff_state.json)

## 1. The question

`docs/ROADMAP.md` keeps one engineering item open: a streaming Cat smaller than the verified
8,254-cell `artifacts/cat_compressed.mal`. The pilot `artifacts/candidate_cat_7893b.mal` is
loader-valid and would save 470 cells, but dies at step 7,372:

```
$ printf '' | ./mb_ref artifacts/candidate_cat_7893b.mal
INVALID_ENCRYPTION: cell 36082 value 29443 step 7372        # exit 3
```

It fails with empty stdin, so this is an execution-path defect, not an I/O defect. What exactly
goes wrong?

## 2. Method

1. A Python interpreter mirroring `oracle/mb_ref.c` (Olmstead semantics, printable-PC stall,
   encryption after every instruction) reproduces the failure bit for bit: cell 36,082, value
   29,443, step 7,372, instruction `i`. Two independent engines agree on the signature.
2. Both programs are run to the moment their program counter reaches the first cell of the
   shifted loop, and the complete states are compared (registers plus every memory cell above the
   image that the reference preamble modified).
3. The comparison is packaged as a reusable gate, `tools/verify_handoff_state.py`.

## 3. The handoff states do not match

The generator cuts the reference at cell 9,067 (its loop entry, reached at step 8,992) and moves
the 315-cell loop slice down by `delta = 1,598 = 17 × 94`, so the candidate must enter its loop at
cell 7,469.

| | reference `cat.mal` | candidate `7893b` |
|---|---:|---:|
| image cells | 9,382 | 7,784 |
| loop entry cell | 9,067 | 7,469 |
| step at entry | 8,992 | 7,371 |
| `a` | 29,524 | 29,521 |
| `d` | 58,975 | **97** (required: 57,377) |
| variables installed | — | **0 / 124** |

The failure follows directly from `d`. The first loop instruction is `/` at 7,469; it advances `d`
to 98. The next instruction is `i` at 7,470, which loads the program counter from `mem[98]` =
36,082 — an address outside the 7,784-cell image whose cell is nonprintable. In the reference the
same `i` reads `mem[58,976]` = 9,067 (shifted: `mem[57,378]` = 7,469), which is what makes the loop
loop.

## 4. Why zero variables are installed

The reference spends its preamble writing a variable table in high memory. Measured on the
reference run:

* 185 writes above the image, to 123 distinct cells, from step **1,478** (cell 58,844) onward;
* 124 cells above the image differ from their initial value at the handoff — the extra cell,
  58,923, is modified by instruction encryption, never by `*`/`p`.

Step 1,478 is six steps after cell 1,473, exactly where the generator stops copying and starts
emitting its own operations. The generated chain then performs 141 writes, 65 of them above the
image — and hits **none** of the 124 target cells. Every macro in the generator's table ends with
`j`, which sets `d = mem[d]` to the value just written, so the cell it writes next is the value it
produced, not the address it meant to fill. Nothing in the pipeline ever steers `d` onto a target
address.

The splice state compounds this: at cell 1,473 the reference holds `a = 29,644`, `d = 77`, while
the generator seeds its walk from the constant 29,524 (`curr = 29524`) and never reads the
registers the prefix actually leaves behind.

## 5. Negative experiment: an 8-cell earlier splice does not help

The reference state at cell 1,465 is `a = 29,524`, `d = 72`, `mem[72] = 29,524`, which matches the
generator's assumption exactly. Splicing there (`prefix = clean_cat[:1465]`, preamble 7,447 ops,
same 7,893-byte file, SHA-256 `e6241dba…`) fails *earlier*:

```
NONPRINTABLE_PC: cell 2249 value 39381 step 2151            # mb_ref exit 3, same in the Python mirror
```

Matching the starting value alone is therefore not the missing piece; the chain has to reach the
target addresses as well. The off-by-eight hypothesis is falsified, not repaired.

## 6. What a repair has to satisfy

The gate encodes the necessary conditions, and they are cheap to check before publishing:

1. the candidate enters the loop at `reference_cell - delta`;
2. `a` and `d - delta` match the reference;
3. every reference cell above the image that the preamble modified is installed at `addr - delta`
   with the shift rule applied to its value.

The repository already contains a synthesiser that satisfies all three:
`tools/resynthesize.py` extracts the true handoff state (`extract_target_state`), uses cell 94 as
the `d` pointer with an explicit `set_dest_94_direct`, and ends with `assert d == handoff_d` before
the final jump. That is the implementation that produces the working 8,254-cell
`cat_compressed.mal`. The path below 8,254 cells is to extend that synthesis — or to teach the
macro chain in `generate_compact_cat.py` to steer `d` — not to publish the current chain.

## 7. Changes in this pass

| File | Change |
|---|---|
| `tools/verify_handoff_state.py` | New gate: compares registers, entry cell and every shifted variable; exit 0 match / 1 mismatch / 2 invalid; `--json` |
| `tools/generate_compact_cat.py` | Local scratch (gitignored, not published): now runs the gate before writing and refuses to publish an unverified candidate |
| `tests/test_handoff_state.py` | Six controls: match, unshifted variable, missing variable, `d` mismatch, wrong entry cell, shift-floor boundary |
| `docs/ROADMAP.md`, `docs/CLAIMS.md` | The open item now cites the measured cause instead of "stalls at step 7,372" |

## 8. Claims

| Claim | Status |
|---|---|
| The candidate reaches its loop entry (cell 7,469) at step 7,371 with `d = 97` | **DEMONSTRATED** |
| The candidate installs 0 of the reference's 124 variables | **DEMONSTRATED** |
| The reference's first high-memory write is at step 1,478 (cell 58,844) | **DEMONSTRATED** |
| The generated chain writes 141 cells, 65 above the image, and hits no target | **DEMONSTRATED** |
| An 8-cell earlier splice fails at step 2,151 | **DEMONSTRATED** |
| The current chain cannot publish a candidate (gate refuses) | **DEMONSTRATED** |
| A streaming Cat smaller than 8,254 cells exists | **NOT_DEMONSTRATED** — still OPEN, nothing published |
| The gate is *sufficient* for program equivalence | **NOT_DEMONSTRATED** — it is necessary only; the loop must also be exercised |
| The reference's variable table is reproduced by the candidate | **REFUTED** (0/124) |

Scope: measurements come from `oracle/mb_ref.c` and one Python mirror that agrees with it on every
failure signature reported here. No third engine was used, and no exhaustive input space was
tested. The pilot artifact and its generator are gitignored scratch
(`artifacts/candidate_cat_*.mal`, `tools/generate_compact_cat.py`): the published result is the
gate plus the measured numbers, not a candidate program.

## 9. Reproduction

```bash
cd <repo root>
./mb_ref artifacts/candidate_cat_7893b.mal </dev/null ; echo "exit=$?"   # 3, cell 36082, step 7372

python3 tools/verify_handoff_state.py \
  --reference reference/malbolge_org/cat.mal --reference-cell 9067 \
  --candidate artifacts/candidate_cat_7893b.mal --delta 1598 \
  --json docs/evidence/2026-10-23-compact-cat-diagnosis/handoff_state.json   # exit 1

python3 -m unittest tests.test_handoff_state -v                            # 6 tests, exit 0
python3 tools/generate_compact_cat.py   # local scratch only: stops at the gate, writes nothing
```

## Erratum (2026-10-24): the gate's layout model

The gate used in this report modelled a **shift-all** layout: the program counter, the `d` register
and the high-memory variable table all move down by `delta`. The working synthesizer
(`tools/resynthesize.py`) uses a **keep-high** layout instead: only the program image moves; the
high-memory workspace keeps its original absolute addresses and only values that address the
shifted suffix are decremented.

`tools/verify_handoff_state.py` now supports both modes and defaults to `keep-high`. The control
that separates them is the published, byte-verified artifact:

* `artifacts/cat_compressed.mal` → 124/124 variables, `HANDOFF MATCH` under `keep-high`;
* the same file → 0/124, `HANDOFF MISMATCH` under `shift-all`.

Consequences for this report:

* The failure of `candidate_cat_7893b.mal` is **unchanged and still real**: under `keep-high` the
  pilot reaches cell 7,469 at step 7,371 with `a = 29,521` (required 29,524), `d = 97` (required
  **58,975**, not 57,377) and 0/124 variables.
* The "0 / 124" figure is confirmed under both models, but under `shift-all` it compared the wrong
  addresses, so it was right by accident.
* The required `d` value quoted above (57,377 = 58,975 − 1,598) is an artefact of the shift-all
  layout. The correct requirement is 58,975.

Follow-up with the corrected gate and a smaller working artifact:
`docs/evidence/2026-10-24-compact-cat-k15/REPORT.md`.
