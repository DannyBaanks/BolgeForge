# K2 C-branch seam I — the Q/C divergence is one `i`, and one mirrored byte edit re-routes C into the print loop

Date: 2026-10-18 · Stage: `K2_C_BRANCH_SEAM_20261018_I`
Suite: `experiments/cat_quine_kaleidoscope/tools/test_k2_psi_seam.py` (8 tests, exit 0)
Candidate under test: `experiments/cat_quine_kaleidoscope/work/candidate_selector_m281.mal`
(`7cab1285…`, the M3 selector; params `y=124, m=64, zQ=89, zC=122, S=187, LQ=44, LC=40, Z=36`)
Supersedes: stage `H` of this family (aborted before `results.json` was written — see §6)

## 1. What Sol's handoff got wrong, and what it got right

`K2_ALGEBRA_EOF_AUDIT_20261018_D` named the next step as "the `d` routing" for the
stored-byte witnesses. Stage `K2_PSI_ROUTE_20261018_E` §1 showed those particular
witnesses cannot be realised at all: no `op`-row composition inverts the store
digit-wise except `(4,8)`, whose inverse `(4,5,3,7,8,6,1,2,0)` is outside the
verified-complete 207-map closure.

The `d`-routing idea itself was right, and it is smaller and closer than it looked.
The M3 selector's two branches are **not** two program halves: they share all 25,531
first instructions and differ at exactly one datum.

## 2. The seam, measured

Both branches reach cell `25646` at step 25,531 and execute `i` (`c = mem[d]`, and
Classic advances `c` afterwards, so the real resume point is `mem[d] + 1`):

| branch | `d` at the branch | `mem[d]` | resumes at | behaviour |
|---|---|---|---|---|
| Q | 26408 | **25975** | 25976 | print loop: 62,239,932 steps, 53,562 bytes, byte-exact quine |
| C | 34 | 35 | 36 | planted `v`: halt at 25,533, 0 bytes |

The 26408 cell is not branch-specific: `mem[26408] = 25975` in **both** runs. So the
value the branch needs is already sitting in the image, and the only difference is
where `d` points. `d = 26408` itself is minted one step earlier: Q's `*` rotates cell
154 (`rot(20173) = 26407`), `j` reads it, `o` increments to 26408. C's `*` was
engineered to hit a different cell: `S = zC + 154 - zQ = 122 + 154 - 89 = 187`, leaving
`mem[154] = 20173` untouched and routing `d` into the literal chain `188 → 34`.

That identity is the whole lever: **`S = 154` exactly when `zC = zQ`.**

## 3. The positive control

Setting `zC := zQ = 89` is one logical byte edit. It must be written twice — at the
plant cell 40 and at its mirror 40 + 26,414 = 26,454 — because the QUINE branch prints
the mirror copy (the `apply_edits` rule `cell + 26414 < 52826` in `selector_dev.py`).
Measured on the compiled `mb_ref` (`bbfedc87…`):

| | baseline `zC=122` | edited `zC=89` |
|---|---|---|
| Q | 53,562 bytes, `== source` ✓ | 53,562 bytes, `== source` ✓ (sha `8622e37c…`) |
| C | 0 bytes, halt at 25,533 | **53,562 bytes, `== source`, 62,239,932 steps** |
| `stdin reads` | preamble=1 loop=0 | preamble=1 loop=0 |

So the C half of the selector is reprogrammable from "halt" to "runs the print loop"
by a single mirrored byte, with the QUINE half still printing itself byte-for-byte.
This is the first demonstrated write against the C branch of this candidate; until
now the only C-branch behaviour on record was the engineered halt.

## 4. The mirror is load-bearing, not cosmetic

A control run edited cell 40 alone and left 26,454 at 122. The quine then printed its
own image **wrong at exactly one byte**: `cmp` reports position 40, printed `122`
against source `89`, and nothing else differs across all 53,562 bytes. That converts
the mirror convention from a build-rule into a measured invariant, and it gives every
later C-branch edit a cheap falsification test: the QUINE row must be byte-exact or
the edit is wrong in a known way.

## 5. What this is not

`C` now prints its own image, not the payload: `edited_C_equals_payload = false`, and
the payload does not appear anywhere in the output. `stdin reads: loop=0` says why —
the print loop never touches stdin, so entering it cannot echo anything read later.
K2 (one program satisfying both the QUINE and CAT rows) is still NOT_DEMONSTRATED, and
the two open problems are now precisely located:

1. **Read/store:** the C branch needs a loop that takes `/` bytes into cells. The
   reroute shows the entry machinery is reachable; the loop body is not built. The
   rearm-free resources for it are the three `rot`-fixed reservoirs (`0`, `29524`,
   `59048`) catalogued in `K2_PSI_ROUTE_20261018_E` §3.
2. **Print what was stored:** the Q loader prints image cells; making it print stored
   payload requires the ψ/R4 recovery that stage E proved exists for bytes
   (`psi = op(59048, ·)` and `R4 = op(·, 29524)` are both involutions) but not through
   a class-collapsing gate.

Next falsifiable milestone: from the C branch's `d` state, a `j` chain onto one of the
47 cells whose value is a print-loop rail address (measured identical in both branches
at this step), with the QUINE row re-checked byte-exact after each mirrored edit.

## 6. Reproduction and stage hygiene

```bash
cd <repo root>
python3 -B experiments/cat_quine_kaleidoscope/tools/test_k2_psi_seam.py \
  --evidence experiments/cat_quine_kaleidoscope/evidence/<NEW_DIR>
```

Requires `cc`; the evidence directory must not exist and files are written `xb`, so no
existing report or artifact is overwritten. Recorded paths are repo-relative and the
temporary oracle builds appear as `<tmp>/<basename>`.

Stage `H` was created by the first run of this suite: the report block read the oracle
binaries and the edited candidate from the temporary directory *after* unittest's
`addClassCleanup` had removed it, so `results.json` was never written. `H/` holds only
`verification.txt` (8 tests, OK) and is kept verbatim rather than deleted or reused;
`I` is the same suite with the hashes and the candidate image captured during
`setUpClass`.
