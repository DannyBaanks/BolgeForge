# K2 rail read M — the print loop can be made to read stdin (20 of 58 rail cells), and reading is not echoing

Date: 2026-10-18 · Stage: `K2_RAIL_READ_20261018_M`
Suite: `experiments/cat_quine_kaleidoscope/tools/test_k2_rail_read.py` (7 tests, exit 0, 1.6 s)
Candidate under test: `experiments/cat_quine_kaleidoscope/evidence/K2_C_BRANCH_SEAM_20261018_I/candidate_psi_route_m281.mal`
(`8622e37c…`, the M3 selector with `zC := zQ = 89`)
Supersedes: stages `K` and `L` of this family, both aborted before usable evidence was written (§7)

## 1. The question

Stage `K2_C_BRANCH_SEAM_20261018_I` moved the C branch into the print loop and left two
open problems, the first being a read/store loop. Before building one, the mechanical
question is whether a read instruction is **reachable inside the running loop at all**:
the loop is 25,531 steps of committed rail, and an image edit has to survive both the
XLAT2 self-modification of the instruction cell and the loader's use of `a`.

Method: trace the loop phase of the stage-I candidate, take every cell the instruction
pointer visits in a 400,000-step window, flip each one (mirrored at `cell + 26414`, the
rule stage I measured as load-bearing) to the value whose rotating decode is `/`, run,
and count reads **per phase**.

## 2. Control: the seam and the phase split

Every run carries `-f 25976`, so the tracer's phase-A/phase-B split is the loader/loop
split, and the trigger is recorded:

| run | trigger step | trigger cell | prints | `preamble` reads | `loop` reads | byte-exact |
|---|---|---|---|---|---|---|
| baseline, full (62,239,932 steps) | 25,532 | 25,976 | 53,562 | 1 | **0** | ✓ |
| baseline, screened (425,532 steps) | 25,532 | 25,976 | 343 | 1 | 0 | ✗ (cut off) |

The trigger step/cell independently confirm the stage-I seam: the shared `i` at cell
25646 executes at step 25,531 and the loop resumes at 25,976. `loop reads = 0` is the
baseline fact this stage attacks — the quine never touches stdin after its one loader read.

## 3. What a single mirrored `/` edit does

60 cells are visited by the loop in the window; 58 of them have their mirror inside the
52,828-cell image and are therefore editable under the mirroring rule.

| outcome of one mirrored read-flip | cells | reads |
|---|---|---|
| **loop phase reads stdin** | **20** | 1–15 in the screen window |
| loader phase only | 12 | extra reads before step 25,532 |
| inert — cell rewritten before its first fetch | 12 | none |
| no extra read | 14 | none |

So `the print LOOP executes `/`` is **DEMONSTRATED**: 20 of 58 rail cells, e.g. cell
26098 gives 15 loop reads in 49,246 steps, cell 25947 gives 14 within the 425,532-step
screen. This is the first positive reachability result for a read inside the C-branch
loop; stages E and I had only shown halts.

The 12 inert cells falsify the assumption that an image edit at a visited cell changes
anything: for all 12, the letter the machine fetches differs from the letter in the image
(26192 image `v` / executed `j`, 26193 `v`/`i`, 26197 `v`/`i`, 26291 `v`/`i`, …), because
the loader rewrites the instruction cell before its first fetch. The handoff's
self-modification warning, measured rather than assumed.

## 4. Reading is not echoing

Each of the 20 loop-reading cells was then run to completion (70,000,000-step cap) with
81 stdin bytes (`Q` then 40..119):

- 18 halt on a planted `v` between 25,537 and 49,427 steps, printing 0–9 bytes.
- 2 run the loop essentially to the end: cell **25975** prints 53,606 bytes in
  62,203,999 steps with **776 loop reads**; cell **25947** prints 52,829 bytes in
  62,221,607 steps with **2,201 loop reads**. Both print the image head (`98 116 38 65 …`)
  and both fail `SANITY out==src` — 53,067 and 52,181 differing positions against the
  source, respectively. They read the whole 81-byte payload and then keep hitting `/`
  against EOF (59048), which is what 776 and 2201 reads mean.
- **0 of 20** print a contiguous run of eight or more of the bytes they were fed. The
  longest payload run found in any output is 0 by the suite's threshold.

`byte_exact` and `reads > 0` are mutually exclusive for every single edit tested. The
reason is structural and visible in the engine source: `/` writes `a`
(`a = (in_ch == EOF) ? 59048 : in_ch`) and `<` prints `a & 255` — one register serves the
loader's live pointer and the output, so a read anywhere on the rail destroys whatever
the next print was about to emit. The loop-reading flips break the accumulator, not the
rail: the runs that keep going keep printing image bytes.

## 5. A capacity constraint on the naive design

Measured on disk, clean-cell footprints (bytes in 33..126, the cells the loader installs):

| program | clean cells |
|---|---|
| stage-I candidate (quine image) | 52,828 |
| `reference/malbolge_org/cat.mal` | 9,382 |
| `artifacts/microcat.mal` | 9,382 |
| `artifacts/cat_compressed.mal` | 8,254 |
| `artifacts/candidate_cat_7893b.mal` | 7,784 |

Classic is 3^10 = 59,049 cells, so this quine leaves **6,221** cells outside its image,
and the smallest committed cat program needs 7,784. Appending a known cat loop to this
quine does not fit the machine; K2 needs either an echo loop under 6,221 cells or a
shorter quine. This is arithmetic on measured sizes, not a proof that no such loop
exists — the 3-cycle witnesses in `K2_STORE_DEPTH_20261018_J` §4 are exactly the kind of
short read/store machinery that could.

## 6. Claims

| claim | status |
|---|---|
| the loop resumes at 25,976 one step after the shared `i` (trigger, re-measured) | DEMONSTRATED |
| the print **loop** executes `/` on stdin after one mirrored rail edit (20 of 58 cells, up to 2,201 loop reads in a full run) | DEMONSTRATED |
| no single mirrored rail edit yields a byte-exact quine that also reads | DEMONSTRATED |
| no single mirrored rail edit echoes ≥ 8 consecutive stdin bytes | DEMONSTRATED |
| rail cells rewritten before their first fetch cannot be routed by an image edit | DEMONSTRATED |
| every loop-reading flip ends on a planted `v` (none runs to `max_steps`) | DEMONSTRATED |
| a two-edit read-then-restore cycle that keeps the quine byte-exact | NOT_DEMONSTRATED |
| storing a read byte into a cell the loader later prints | NOT_DEMONSTRATED |
| an executable C-branch read/store loop | NOT_DEMONSTRATED |
| C echoes stdin bytes (CAT row) / single program with both rows (K2) | NOT_DEMONSTRATED |

Scope note: every number here comes from the one compiled tracer (`<tmp>/trace_loop`,
`7f92b594…`). No flipped program was re-run against `oracle/mb_ref.c` or the Python model,
so cross-engine parity for the flips is untested; only the stage-J parity control covered
byte routing on the unmodified candidate. Cell 26395 is the one loop-reader whose edit
also changes the loader's read count (3 instead of 1), so "the loader still read exactly
once" holds for 19 of 20, and the suite records it as a count rather than an invariant.

## 7. Stage hygiene: what K and L got wrong, and what survives them

Two earlier runs of this suite produced directories that are kept verbatim and are **not**
the evidence of this stage:

- `K2_RAIL_READ_20261018_K/` — only `verification.txt`. The report block read the tracer
  binary from the temporary tree after `addClassCleanup` had removed it.
- `K2_RAIL_READ_20261018_L/` — `results.json` records `errors=4` and null measurements.
  Two distinct defects: (a) the same temp-dir read, fixed by capturing
  `tracer_sha256` during `setUpClass`; (b) the real one — unittest sorts method names
  alphabetically, so `test_flipping_a_visited_rail_cell…` ran before
  `test_loop_visits_a_bounded_set_of_rail_cells` and consumed attributes that did not exist
  yet. All measurement now happens in `setUpClass`; the tests only assert over it.

Stage L also carries a third, subtler error that this report corrects in prose: a scratch
scan from stage K reported **32** read-gaining rail cells. That count came from runs
without `-f`, and without a trigger cell the tracer never sets `loop_active`, so loop-phase
reads were tallied into the preamble counter. Split by phase, the 32 become **20 loop
readers + 12 loader-only**. The claim "the print loop can read" would have been unsupported
under the K/L counting; it is supported now. Raw files in K and L are not edited. They are **preserved on the workstation and not
committed**: each transcript carries four traceback lines with the absolute workstation
path, and the installed Repo Engine gate blocks a commit on any finding, INFO included
(`REPO ENGINE: BLOCKED (staged) … [INFO] LOCAL_PATH_001_DOC …/K2_RAIL_READ_20261018_K/verification.txt
— private workstation path … Nothing was published`). The three files of this stage are
path-clean (0 hits for the private prefix in `results.json`, `verification.txt`,
`REPORT.md`), so the committed evidence is the usable stage and the aborted transcripts
stay where a human can still read them. Clearing them for publication would need a
`.repo-engine-exceptions.toml` entry, which this repo deliberately does not carry.

## 8. Reproduction

```bash
cd <repo root>
python3 -B experiments/cat_quine_kaleidoscope/tools/test_k2_rail_read.py \
  --evidence experiments/cat_quine_kaleidoscope/evidence/<NEW_DIR>
```

Requires `cc`. The evidence directory must not already exist; nothing is overwritten.
Recorded paths are repo-relative and the temporary tracer build appears as
`<tmp>/trace_loop`.

## 9. Next falsifiable milestone

Single edits are exhausted: the register conflict is the wall, not reachability. The next
test is a **two-cell mirrored edit set** — a `/` on a loop rail plus a second edit that
restores the accumulator before the next `<` (the rail is 3-cycle per byte for
store/recover depth, `K2_STORE_DEPTH_20261018_J` §2). Falsification criterion unchanged:
the QUINE row must come out byte-exact, or the edit is wrong in a known position.
