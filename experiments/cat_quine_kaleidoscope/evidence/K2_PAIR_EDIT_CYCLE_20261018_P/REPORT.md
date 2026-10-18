# K2 pair edit P — a two-cell edit reads AND stores inside the print loop, puts one stdin byte on stdout, and still cannot recover it

Date: 2026-10-18 · Stage: `K2_PAIR_EDIT_CYCLE_20261018_P`
Suite: `experiments/cat_quine_kaleidoscope/tools/test_k2_pair_edit_cycle.py` (11 tests, exit 0, 4.99 s)
Candidate under test: `experiments/cat_quine_kaleidoscope/evidence/K2_C_BRANCH_SEAM_20261018_I/candidate_psi_route_m281.mal`
(`8622e37c…`, the M3 selector with `zC := zQ = 89`)
Supersedes: stage `N` of this family (mis-attributed events) and two intermediate re-seals `O`, `O2` (§12)

## 1. The question

Stage M showed that one mirrored rail edit can put a `/` inside the running print loop, and
that reading is not echoing: `/` writes the accumulator `a`, and `a` is exactly what the
loop's `<` prints, so a read in the print loop is structurally destructive. The handoff's
next step was to route `d` and test repeated store/restore/rearm cycles "taking instruction
self-modification into account". The approved milestone was therefore: **two** mirrored
cells — a read on a rail plus something in the next cell — re-verifying the byte-exact QUINE
row after every edit.

This stage measures that instead of designing it. For every pair of cells the instruction
pointer visits in consecutive steps of the loop phase, edit the first to `/`, the second to
each of seven letters, and ask three separate questions:

* **dynamics** — does a read→store cycle execute, at which cells, and does the stored value
  depend on the stdin byte?
* **information** — can the byte be recovered from what was stored, for one store and for two?
* **output** — does a stdin byte ever reach stdout, and how long a run of them?

## 2. Control: the seam, the phase split, the byte-exact baseline

Every run carries `-f 25976`, so the tracer's phase-A/phase-B split is the loader/loop split.

| run | trigger step | trigger cell | prints | preamble reads | loop reads | byte-exact |
|---|---|---|---|---|---|---|
| baseline, full (62,239,932 steps) | 25,532 | 25,976 | 53,562 | 1 | 0 | ✓ |

The baseline is the invariant the milestone is measured against: the candidate still prints
its own 53,562 bytes and never touches stdin after the loader read.

## 3. Geometry: which pairs the loop steps through

A 400,000-step loop-phase trace of the **unmodified** candidate gives 400,000 traced steps
and **38** pairs `(c, c+1)` where the instruction pointer really moves one cell per step at
or after the loop-entry cell and both mirrors stay inside the 52,828-cell image.

| pair | visits in the window |
|---|---|
| 26098 → 26099 | 23,611 |
| 26298…26304 → next | 12,226 each |
| 26101 → 26102 | 5,106 |
| 26008 → 26009 | 2,545 |
| 26286 → 26287 | 1,527 |
| 26004 → 26005 | 18 |

## 4. What a two-cell mirrored edit set does

38 pairs × 7 successor letters (`p * < j i / o`) = **266** pair runs, screened at 425,532
steps with a 24,500-step loop trace each.

| outcome | runs |
|---|---|
| read executes in the loop phase | **76** |
| a `p`/`*` store executes within 8 **steps** of a read | 63 |
| a store executes exactly **1 step** after a read (a real cycle) | **7** |
| — of which the cycle runs at the two edited cells | **3** |
| — of which the cycle runs elsewhere (collateral) | 1 |
| — of which the store is `p` (byte operand) / `*` (rot, no byte) | 4 / 3 |

At an edited pair, only `p` and `*` store one step after the read; `<`, `j`, `i`, `/`, `o`
produce no immediate store. So "**a two-cell edit set reads a byte and writes memory in the
same cycle of the print loop**" is DEMONSTRATED — the mechanism Sol asked about exists.

## 5. Attribution: the cell edited is not the cell executed

This is the correction that moved the numbers. Stage N labelled every event with the edited
cell and treated consecutive trace **lines** as consecutive **steps**. Both are wrong here:

* the tracer skips any step whose instruction cell holds a value outside 33..126, so line
  distance ≠ step distance. `MAX_STORE_GAP` is now measured in steps from the trace header.
* a two-cell edit reroutes the trajectory. The one collateral cycle proves it: editing cells
  26286/26287 makes the read execute at **35982** and the store at **35983** — cells the edit
  never touched, where the quine image already holds a `/` followed by a `p` — storing into
  data cell **79** (`14418 → 36288`). Edited cell, executed cell and the store's data cell are
  three different numbers and are recorded separately for all eleven cycle/control rows.

The consequence for the algebra is not cosmetic: with correct attribution the set of cell
states actually reached by a live cycle is `{100, 14418, 26101, 26400}`, and state `82` is not
in it. §8 shows what that does to the headline result of stage N.

## 6. The cycles on the edited pair

| edit | read executes | store executes | stores into | old | new | `== crazy(byte, old)` |
|---|---|---|---|---|---|---|
| `/`@26004 + `p`@26005 | 26004 (step 25,534) | 26005 (25,535) | 26412 | 100 | 29,502 | ✓ |
| `/`@26008 + `p`@26009 | 26008 (25,545) | 26009 (25,546) | 26218 | 26,400 | 29,556 | ✓ |
| `/`@26101 + `p`@26102 | 26101 (25,536) | 26102 (25,537) | 26209 | 26,101 | 32,661 | ✓ |

Each read consumed stdin byte 40, the second byte of the payload (the first, 81 = `Q`, is the
branch discriminator taken by the loader). In all three the store's data cell is neither of
the two edited cells — `d` has moved on, which is exactly the routing the handoff asked about.

## 7. Byte dependence, tested twice

Predicting `new == crazy(byte, old)` could be an operand-order coincidence (trap T24), so each
of the 7 immediate-store runs was replayed with stdin byte 40 replaced by 187 and re-attributed
under the probe. All 7 reproduced the same cycle (same executed cells, same `old`, same op,
byte 187):

| edit | op | stored under byte 40 | stored under byte 187 | moved? | matches prediction |
|---|---|---|---|---|---|
| 26004 + `p` | p | 29,502 | 29,601 | **yes** | ✓ |
| 26008 + `p` | p | 29,556 | 29,634 | **yes** | ✓ |
| 26101 + `p` | p | 32,661 | 32,760 | **yes** | ✓ |
| 26286 + `i` (collateral, at 35982/35983) | p | 36,288 | 36,396 | **yes** | ✓ |
| 26004 + `*` | * | 19,716 | 19,716 | no | ✓ `rot(old)` |
| 26008 + `*` | * | 8,800 | 8,800 | no | ✓ `rot(old)` |
| 26101 + `*` | * | 28,383 | 28,383 | no | ✓ `rot(old)` |

The `*` rows are the control that makes the `p` rows mean something: "the stored value depends
on stdin" is a property of `p`, not a property of "the trace changed". 3 of the 4 byte-moving
stores are on the edited pair.

## 8. The information wall: one store does not determine the byte

A census of **all 59,049** cell states × the 257-element storage domain (bytes 0..255 plus
59048, the value `/` yields at EOF), computed on base-9 digits and cross-checked against direct
`crazy_op` evaluation on a stride-211 sample plus every measured state and reservoir
(mismatch list `[]`):

| measure | value |
|---|---|
| cell states where one store IS injective | **162** of 59,049 |
| worst case, candidate bytes for one observation | 39 |
| most common outcome | 184 or 208 of the 257 inputs collapsed (6,480 states each) |
| worst collapse | 224 of 257 lost (2,592 states) |

`histogram_bytes_collapsed_to_states[k]` counts cell states for which one store collapses `k`
of the 257 possible inputs; `k = 0` is the 162 injective states. The four states a live cycle
reached, and the three values `rot` fixes:

| old | distinct outcomes | worst-case candidates |
|---|---|---|
| 100 | 79 | 8 |
| 14418 | 49 | 16 |
| 26101 | 73 | 8 |
| 26400 | 79 | 8 |
| 0 | 40 | 32 |
| **29524** | **257** | **1** |
| 59048 | 33 | 39 |

Repeating the store into the **same** cell never narrows this (worst-case candidates
8→48, 16→32, 8→48, 8→72, 32→32, and the injective 29524 loses injectivity 1→33; 59048 goes
39→257 candidates collapsing to a single distinct outcome). Two bytes stored into one cell:
66,049 possible pairs land in 296–603 distinct finals, up to 3,813 pairs per final.

## 9. Joint injectivity: reservoir or nothing

Two stores of the **same byte** into two **different** cells were pair-tested over the 4
measured states + 3 reservoir values (49 pairings). **15** reach all 257 outcomes — and every
one of them contains 29524, or pairs 0 with 59048. Among the 16 measured-measured pairings the
best is **172 of 257** outcomes.

This directly retracts stage N's most quotable claim. N reported a rail-rail exception,
`(82, 26400) == 257`; state 82 only appeared because N attributed the collateral cycle to the
edited cell 26286 instead of the executed cell 35982. With the attribution fixed there is **no
reservoir-free pairing** in the tested set, and the honest statement is the weaker one:
byte recovery by double storage is an algebraic possibility that requires a cell holding one of
the three values `rot` fixes — and no run in this stage put any loop-reachable cell into 29524.

## 10. The output side: one stdin byte does reach stdout

The `<` successor puts a print in the cell right after the edited read, which is where the
accumulator still holds the byte just read. 11 reading `<` runs were probed at the full cap;
the byte identity is shown **causally**, not by arithmetic:

| status | runs | detail |
|---|---|---|
| **stdin byte echoed** | **3** | cells 26004, 26008, 26101: print `[40]` under the payload, print `[187]` under the probe |
| print is not the stdin byte | 2 | 26293, 26400 print image bytes `98,116,38…` — the loop printed before the read |
| no output | 6 | read in the loop, nothing printed |

Across all 76 full runs the longest consecutive stdin run ever echoed is **1 byte**
(distribution `{0, 1}`). So stage M's "reading is not echoing" wall is now measured rather than
assumed: the mechanism can deliver a single byte, and one byte is what the accumulator can hold
while the loop keeps its own `a`.

## 11. Why the QUINE row still breaks

All 76 reading pair runs were executed to completion at the 70,000,000-step cap:
**0 byte-exact**, 0 with `head_equals_image`, 0 echoing ≥ 8 bytes, prints 0–9 bytes,
25,537–49,427 steps, every run halting on a `v`, max 15 loop reads. The three on-edit cycles
halt 2–140 steps after their store: the read overwrote the accumulator the loop prints, and
none of the seven successor letters restores it before the next `<`. That is the milestone's
restore half, and it stays `NOT_DEMONSTRATED`.

## 12. Claims

| claim | status |
|---|---|
| a two-cell mirrored edit set executes a read and a store one step apart **at** the edited cells (3 cycles, stored value `== crazy(byte, old)`) | DEMONSTRATED |
| the value stored at that edited pair moves with the stdin byte (3 reproduced runs) | DEMONSTRATED |
| byte dependence across every immediate-store run (4 of 7 reproduced under the probe) | DEMONSTRATED |
| `*` successors store, but byte-independently: every reproduced rot store kept `rot(old)` (3 runs) | DEMONSTRATED |
| a read→store cycle can execute at cells the edit never touched (1 of 4, at 35982/35983) | DEMONSTRATED |
| one `p` store does not determine the byte (162 of 59,049 states injective, worst case 39 candidates) | DEMONSTRATED |
| a second store into the same cell never narrows the byte, and often widens it | DEMONSTRATED |
| two stores into distinct cells are jointly injective **only with a reservoir state** (15 of 49 pairings, all containing 29524 or 0×59048) | DEMONSTRATED |
| no pairing of two ordinary reached states recovers the byte (best of 16: 172/257; N's `(82, 26400)` was mis-attribution) | DEMONSTRATED |
| the C branch can put a stdin byte on stdout, shown by replacing that byte (3 edit sets) | DEMONSTRATED |
| the echo is exactly one byte long (max over 76 full runs = 1) | DEMONSTRATED |
| no two-cell edit set yields a byte-exact quine | DEMONSTRATED |
| no two-cell edit set echoes eight or more consecutive stdin bytes | DEMONSTRATED |
| a program that performs the jointly injective double store on one byte | NOT_DEMONSTRATED |
| the machine ever puts a loop-reachable cell into the 29524 reservoir state | NOT_DEMONSTRATED |
| a read/store/**restore** cycle that keeps the QUINE row | NOT_DEMONSTRATED |
| an executable C-branch read/store loop | NOT_DEMONSTRATED |
| C echoes a **run** of stdin bytes (what the CAT row needs) | NOT_DEMONSTRATED |
| single program satisfying both QUINE and CAT rows (K2) | NOT_DEMONSTRATED |

Explicitly not demonstrated, beyond the table: that a reservoir-free pairing is impossible *in
general* (49 pairings tested, not 59,049²; the exhaustive census covers single stores only);
that the collateral cycle is **caused** rather than merely **exposed** by the edit (the
unmodified quine was not traced at 35982/35983); more than one byte stored per read cycle;
two-engine parity (only the compiled tracer ran these programs); that the 6,221 cells outside
the quine image could host a cat loop.

## 13. Stage hygiene

Stage `N` (`K2_PAIR_EDIT_CYCLE_20261018_N`, on disk, uncommitted) is kept verbatim as the
aborted run: its detection measured line distance instead of step distance and labelled events
with the edited cell. Its three defects and their fixes are §5 and §9. `O` and `O2` are
intermediate re-seals of the corrected suite — `O` published a claim its own data contradicted
("most cycles are collateral", actually 1 of 4), and `O2` predates the §10 echo probe. None of
the four directories is reused; `P` is the seal this report describes.

## 14. Reproduction

```bash
cd experiments/cat_quine_kaleidoscope
python3 -B tools/test_k2_pair_edit_cycle.py \
    --evidence evidence/K2_PAIR_EDIT_CYCLE_20261018_P        # refuses an existing directory
```

Requires `cc`. Evidence paths are recorded repo-relative; temporary builds appear as
`<tmp>/<basename>`. Inputs (sha256 at seal time): candidate `8622e37c…`,
`trace_loop.c` `8b202488…`, `selector_dev.py` `da776dd6…`, suite `205b7631…`;
compiled tracer `7f92b594…`. Environment: Linux 7.0.0-38-generic x86_64 glibc 2.39,
CPython 3.12.3. `verification.txt` holds the 11-test run, `results.json` every row
(266 pair runs, 76 full runs, 7 perturbations, 11 echo probes, 59,049-state census with
histogram, 49 joint pairings, all tables).

## 15. Next falsifiable milestone

The mechanism now exists and the wall has moved to the restore. Next: **find or build a cell
state in `rot`'s fixed set reachable by a loop-reachable cell** — that is, route `d` so that a
store lands on a cell already holding 0, 29524 or 59048, then test whether the pair
(reservoir, measured state) jointly determines the byte **in one program** rather than in two
separate runs. If no routing reaches a reservoir, the falsifiable statement is the negative
one: byte recovery in the C branch needs a state the machine cannot reach, and the ψ loop needs
a second register rather than a second store.
