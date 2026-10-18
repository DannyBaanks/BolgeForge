# K2 route audit: lossy-gate recovery is impossible, the psi route is not

Date: 2026-10-18. Scope: Classic Malbolge (3^10), BolgeForge CAT-QUINE Kaleidoscope.
Status: K2 still NOT_DEMONSTRATED. This audit redirects the K2 design; it does not
build an executable CAT branch.
Author: `qoder_catquine_continue_1792325790`. Lane lease taken from
`opencode_catquine_audit_1792324827010476228` under rule L0 (idle 16 m).

All operator claims below were checked against the compiled `oracle/mb_ref.c`
operator through a ctypes shim, not against a second copy of the base-9 table.
Orientation throughout: `op(ctrl, cell)` indexes the table as `O[cell][ctrl]`
(trap T24); the swapped-order control differs.

## 1. The planned next step in audit D is unreachable

Audit D (`K2_ALGEBRA_EOF_AUDIT_20261018_D/REPORT.md`) ended with "realize one
stored-byte witness with actual d routing". Its witnesses come from a family of
programs with this shape: read byte `b`, store it with `p` against a cell holding
`V`, collapse `a` to a class constant with the two-step gate, then recover `b`
from the store cell with further `p` steps against constant cells.

That family cannot recover the byte, at any cost, for any of its 29,914 candidates.

At digit position `j`, with store-row `s = V_j` and landing-column `c = td_j`, the
byte digit `d` reaches the store-cell read as `O[O[s][d]][c]`. A `p` against a
constant operand applies one table row per position, so every continuation is a
composition of table rows. Recovery therefore requires that map to be injective
and that its inverse lie in the row-composition closure.

| Check | Observed result |
|---|---|
| `(s,c)` pairs injective on digits 0..8 | exactly one: `(4, 8)` of 81 |
| Row-composition closure | 207 maps, verified closed under all 9 rows |
| Required inverse of `h_8` | `(4,5,3,7,8,6,1,2,0)` — not in the closure |

Because the closure is verified complete, no length bound is assumed: the
negative holds for every sequence of `p`-against-constant steps. Positions 0 and 1
carry the full digit range, so the single admissible `(s,c)` is forced at both.

**Consequence.** The stored-byte witnesses are not "unrouted programs awaiting d
routing". They are not realisable as programs at all. The blocker is upstream of
addressing, so implementing d routing first would have spent the effort on a dead
branch.

## 2. What the working CAT actually does

`reference/malbolge_org/cat.mal` (Lutter 2012) echoes arbitrary payloads on the
compiled oracle — verified here for all 256 bytes, a text payload and the empty
payload, each byte-exact with `halt=v`. Its loop never destroys the byte, so it
never has to recover it. Two involutions do the work:

- `R4 = op(., 29524)` — constant row, byte as column. Round-trips every byte.
- `psi(v) = op(59048, v)` — byte as row, constant column 8. Also an involution.

The recorded loop trace (`cat_loop_trace.txt`) shows both, and the algebra matches
the trace values exactly:

| Trace step | Operation | Observed |
|---|---|---|
| 9000 | `p` at cell holding 29524, `a=72` | 29524 → 29560 (store) |
| 9015 | `p` at cell holding 29524, `a=29560` | 29524 → 72 (raw byte now parked in a cell) |
| 9273 | `*` at cell holding 59048 | 59048 → 59048, `a=59048` (reservoir, not consumed) |
| 9278 | `p` at the byte cell, `a=59048` | 72 → 36 (`psi`) |
| 9295 | `p` at the same cell, `a=59048` again | 36 → 72 (`psi` is self-inverse) |
| 9306 | `<` with `a=72` | OUT:72 |

`psi(59048) = 29524` while `psi(byte) <= 510` for all 256 bytes, and 29524 is not in
the byte image. So one non-destructive `*` plus one `p` separates EOF from every
data byte with disjoint ranges — without collapsing anything.

## 3. Rearming is solved by the rotation-fixed set

`rot` fixes exactly three values in Classic 3^10: **{0, 29524, 59048}** (verified
over all 59,049). A cell holding one of them can be read with `*` as often as
needed and is left unchanged, so a loop can re-supply these constants forever.
This is the mechanism audit D suspected ("all three control words are
rotation-fixed") and the trace confirms it in use at step 9273.

The K2 candidate already has all three at the branch point
(`work/candidate_selector_m281.mal`, snapshot at step 25,445):

| Value | Cells |
|---|---|
| 59048 | 147, 153, 26171, 26235, 26249, 26325 |
| 29524 | 140, 151, 26208, 26211, 26370 |
| 0 | 150 |

None of the three is present in the loaded image; the preamble mints them, so they
are already inside the deterministic history the QUINE branch reproduces. d routing
by `j` chains is likewise already demonstrated in this image (selector script
25560..25582).

## 4. Open problem for the psi route

Preserving the byte under the branch test is not the same as branching on it. A
`j`-chain plus `i` needs a jump target that is constant per class, and a collapse
that discards the byte is what section 1 forbids — unless the byte has already been
parked where `psi` can fetch it back, which section 2 shows is possible.

The cheapest hoped-for loop would collapse using only the three rearm-free
reservoirs. Searched exhaustively for operand sequences over
{0, 29524, 59048} of length 1..4 that are constant on all 256 data bytes and
different on EOF: **0 hits**. Uniform rows are too coarse — the same
`R0 o R8` that flattens the data digits flattens the EOF digits.

**Next task:** read the branch out of the recorded cat.mal trace instead of
guessing it — determine how cat.mal converts the `psi`-separated ranges into two
distinct `i` targets, and which of those steps are rearm-free. Then port that
discriminator onto the K2 candidate's own reservoir addresses and re-verify the
QUINE half byte-exact after every change to P.

## 5. Claims

| Label | Claim |
|---|---|
| DEMONSTRATED | rot fixes exactly {0, 29524, 59048} in Classic 3^10 |
| DEMONSTRATED | `psi` is an involution on 0..255 and on EOF, with disjoint images |
| DEMONSTRATED | `R4` round-trips all 256 bytes |
| DEMONSTRATED | no `p`-against-constant sequence of any length recovers the byte after a lossy class gate (single-store-cell family) |
| DEMONSTRATED | the 29,914 stored-byte candidates of audit D are not realisable by their intended shape |
| DEMONSTRATED | reservoir constants exist at the candidate's branch point |
| DEMONSTRATED | cat.mal echoes 256-byte, text and empty payloads byte-exact with real halt |
| NOT_DEMONSTRATED | executable K2 (one P satisfying both contract rows) |
| NOT_DEMONSTRATED | a rearm-free discriminator for the psi route on this image |
| NOT_DEMONSTRATED | second independent Classic engine parity (single-engine state unchanged) |

The scope of the section 1 negative is one program family: store through a single
cell, collapse to a class constant, recover through `p` against constants. It does
not forbid recovery through a byte-dependent operand, through `*`, or through a
design that never collapses — section 2 is exactly such a design.

## 6. Evidence and reproduction

`verification.txt` holds the raw unittest output (7 tests, 0 failures, 0 errors,
0 skips). `results.json` holds environment, compiler shim hash, the claims table,
reservoir cell lists, the three cat runs and source hashes.
`cat_loop_trace.txt` is the per-step loop trace of cat.mal on the compiled tracer;
`cat_loop_summary.txt` its coverage header. `hashes.json` binds these files.
Raw stdin/stdout of the selector runs stay in audit D, unmodified.

Reproduce from the BolgeForge root, always in a new evidence directory:

```bash
python3 -B experiments/cat_quine_kaleidoscope/tools/test_k2_psi_route.py \
  --evidence experiments/cat_quine_kaleidoscope/evidence/<NEW>
```

All recorded paths are relative to the repository root; no workstation path appears
in any file produced here.
