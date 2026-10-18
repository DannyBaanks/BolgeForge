# K2 store-depth J — a CAT echo needs two or three read/store cycles, never one

Date: 2026-10-18 · Stage: `K2_STORE_DEPTH_20261018_J`
Suite: `experiments/cat_quine_kaleidoscope/tools/test_k2_store_depth.py` (9 tests, exit 0, 39.5 s)
Candidate: `experiments/cat_quine_kaleidoscope/work/candidate_selector_m281.mal` (`7cab1285…`)
Builds on: `K2_ALGEBRA_EOF_AUDIT_20261018_G`, `K2_PSI_ROUTE_20261018_E`,
`K2_C_BRANCH_SEAM_20261018_I`

## 1. What stage E killed, and what it left standing

Stage E proved that the **digit-wise** stored-byte witnesses are unrealisable: no
composition of `op` rows in the verified 207-map closure inverts the store except
`(4,8)`, whose inverse is outside that closure. That statement is about recovering
a whole 5-trit cell value.

The print condition is weaker, and E never tested it. Both engines emit the
accumulator, not the cell:

```c
mb_ref.c      else if (instr == '<') putchar((int)(a & 255));
trace_loop.c  else if (instr == '<') { fputc((int)(a & 255), outf);
mb_ref.c      else if (instr == 'p') a = mem[d] = op(a, mem[d]);
mb_ref.c      else if (instr == '/') { int in_ch = getchar();
                                       a = (in_ch == EOF) ? 59048 : (unsigned short)in_ch; }
```

So an echo only has to land the *last* stored value in the right residue class
modulo 256, possibly after one `*` rotation. That reopens the route stage E
appeared to close, and this stage measures the reopened gate exactly.

## 2. The gate, measured over every cell value

One `/`+`p` cycle from a cell holding `v` leaves `op(a, v)` for
`a ∈ {0 … 255, 59048}` (257 choices; 59048 is the EOF read, i.e. ψ). The cycle
prints `x & 255` for that stored `x`, or `rot(x) & 255` if a `*` follows.
Coverage of the 256 output bytes, over all 59,049 possible `v`:

| cycles | cell values with full 256-byte coverage | note |
|---|---|---|
| 1 | **148** | the 148 complete values are the *whole* depth-1 result; every other `v` covers at most 255 of 256 bytes (coverage over all `v`: min 46, mean 114.4) |
| 2 | **40,646** | 40,498 of them are not in the 1-cycle set |
| 3 | **59,049** | zero values still short |

`results.json` records the set explicitly: `count = 148`, `lowest = 526`,
`highest = 58927`, `first_16 = [526, 607, 1255, 1336, 2065, 2713, 2794, 3442,
3523, 4252, 4495, 4738, 4981, 5224, 5467, 5710]`, `present_in_candidate_image = 0`.

## 3. The candidate's own image

The M3 selector image holds only 94 distinct cell values (the 94 printable
characters). Against the same gate:

| minimum cycles for the value | image cells | distinct values |
|---|---|---|
| 1 | 0 | 0 of 94 |
| 2 | 7,970 | 13 of 94 |
| 3 | 44,858 | 81 of 94 |

**No cell of this candidate can echo an arbitrary byte through a single read/store
cycle.** Any C-branch loader must chain at least two `p` operations, and three for
81 of the 94 payload byte classes.

## 4. Witnesses, not just counts

Worst case measured: a cell holding `v = 74` covers 243 of 256 bytes after two
cycles; the missing 13 are exactly `206 … 218`. Each has an explicit three-cycle
witness recorded in `results.json`, e.g. target 206:

```
cell 74 -> op(a1,.) = 29440 -> op(a2,.) = 29415 -> op(a3,.) = 58830 ; 58830 & 255 = 206
```

`a1, a2, a3` are stdin bytes (or 59048 at EOF) chosen so the intermediate values
are those cells; the last `rotations = 0` means the value is printed straight from
`p`, no trailing `*` needed.

## 5. Input-domain parity (this is what makes the count meaningful)

The 257-element input domain was checked, not assumed. Model, `mb_ref` and
`trace_loop` agree on which first byte takes which branch:

| stdin byte | model at step 25,532 | `mb_ref` stdout |
|---|---|---|
| 81 | `c = 25976` (Q) | 53,562 bytes |
| 67 | not Q (engineered C halt) | 0 bytes |
| 113 | not Q | 0 bytes |

81 and 113 are congruent modulo 32. If this machine truncated its input to 5 bits
(a claim often made about the canonical Malbolge input instruction), byte 113
would have printed the image. It
prints nothing, so the full 8 bits reach `a`, and `ψ = op(59048, ·)` is exactly
what an EOF read followed by a store does — checked cell-by-cell against
`selector_dev.crazy_op` over all 59,049 values, and as an involution on
`{0, 1, 8, 74, 124, 526, 20173, 29524, 58830, 59048}`. `trace_loop` output for byte
81 is hash-identical to `mb_ref`.

## 6. Design consequence for the C branch

The seam stage I moved C into the print loop; this stage sizes the loop body C
still lacks:

1. a `/`+`p` pair is already present in the preamble (read at 25562, store at
   25570), so the *shape* of one cycle exists in the image; the C branch needs
   **two or three of them chained onto one chosen cell**, then a path back to the
   loop head, then a print.
2. chained cycles need the intermediate cell values, and those are what the
   witnesses in §4 name (29440 → 29415 → 58830 for target 206). Whether the C
   branch can *address* those values is the rail question, not an algebra
   question: NOT_DEMONSTRATED here.
3. EOF is a free operand: reading at EOF puts 59048 in `a`, so `p` becomes ψ, an
   involution. A loop that reads past the end can therefore undo its own last
   store — the rearm mechanism asked for in the handoff, now with a concrete
   operand instead of a wish.

Next falsifiable milestone: hold the payload fixed and exhibit, for one chosen
print cell, an address sequence of `j`/`o` rail states that executes `/`,`p`,`/`,`p`
(or three cycles) onto that cell and then reaches a `<`, with the QUINE row
re-checked byte-exact after every mirrored edit. If no such rail sequence exists
for the 81 three-cycle byte classes, the candidate family is dead and a new
discriminator geometry must be searched.

## 7. Claims

| claim | status |
|---|---|
| `<` prints `a & 255`, `/` loads a raw byte or 59048, in both engines | DEMONSTRATED |
| ψ = op(59048, ·) is the EOF-read-plus-store action, an involution | DEMONSTRATED |
| exactly 148 cell values print every byte after one cycle; none occurs in this image | DEMONSTRATED |
| two cycles suffice for 40,646 of 59,049 values | DEMONSTRATED |
| three cycles suffice for every value (0 short) | DEMONSTRATED |
| the worst two-cycle gap (v = 74, bytes 206–218) has explicit three-cycle witnesses | DEMONSTRATED |
| model and `mb_ref` agree on which of bytes 81 / 67 / 113 takes which branch | DEMONSTRATED |
| `trace_loop` and `mb_ref` give identical output bytes for the byte-81 run | DEMONSTRATED |
| an executable C-branch read/store loop | NOT_DEMONSTRATED |
| C echoes stdin bytes (CAT row) | NOT_DEMONSTRATED |
| one program satisfying both QUINE and CAT rows (K2) | NOT_DEMONSTRATED |

Scope note, so this table and `results.json` are read the same way: the
`claims` string in `results.json` for the routing row names all three engines in
one phrase, and the evidence behind it is asymmetric — the byte→branch agreement
was tested model↔`mb_ref` for the three bytes, while `trace_loop` was checked for
output equality against `mb_ref` on the byte-81 run only. The two rows above are
the per-test statement; `results.json` is left exactly as the suite emitted it.

## 8. Reproduction

```bash
cd <repo root>
python3 -B experiments/cat_quine_kaleidoscope/tools/test_k2_store_depth.py \
  --evidence experiments/cat_quine_kaleidoscope/evidence/<NEW_DIR>
```

Requires `cc`; the evidence directory must not exist and files are written `xb`, so
nothing already on disk is overwritten. Recorded paths are repo-relative and the
temporary oracle builds appear as `<tmp>/<basename>`. The algebra pass costs ~38 s
of the 39.5 s; it is a full sweep over 59,049 cell values, so the counts in §2 and
§3 are exhaustive, not sampled.
