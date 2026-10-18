# m=299 resynthesis — status 2026-10-15 [NOT_DEMONSTRATED: no sub-59,852 quine exists yet]

> **CORRECTION 2026-10-16:** sub-59,852 quines now EXIST and are verified. See the
> "Session 2026-10-16" section at the bottom: m=284 (54,134 B), m=293 (55,850 B),
> m=308 (58,709 B), all mb_ref 0-byte-diff. `m299_candidate_56993b.mal` is INVALID
> (mb_ref emits 0 bytes).

Goal: classical Malbolge quine < Lutter's 59,852 bytes (C = 94*m cells per half, Lutter m=314).
Loop synthesis for m=299 (56,993 bytes) is verified in simulation (66M steps, bit-exact) when
the 215 loop variables are pre-initialised. The missing piece is the PREAMBLE that writes them.

## What was tried and failed
* Stock-LMAO clone (`/tmp/lmao_custom` + `test_full_quine_fp.c`): generator converges in 2
  iterations but the program halts after 5 outputs (final `i` reads mem[116]=37131).
  Cause: stock LMAO returns to module 0 through cells holding 81 (d=81 -> 82). Lutter's
  quine does not.

## How Lutter's preamble actually works (measured from a full trace, `lt.py`)
* Module 0 lives at cells 140..158 (not 82). DESTINATION register = cell 148 (starts 29265, +9 per
  9-cell group via INCREMENT_BY_9 using mask cells 143..146 and scratch 142). tmp = cell 154,
  rot/crazy chains through cells 150(C0) 151(29524) 152(59046/59047) 153(C2); pointers at
  141(->147) 149(->139) 155(->152) 156(->149) 157(->146).
* Return from a write: variable cells carry text chars c(X)=K-X (all decode to `o`);
  `j` on such a cell lands in a 94-cell landing table (cells 45..138) whose entries are 139,
  then d=139 -> module 0 at 140. The table is overwritten at the very END of the preamble
  (steps >= 21600) with 29420 (a loop pointer) — so the loop later uses it as return table.
* Because 1410 = 15*94, all loader opcodes and ladder chars are invariant under the shift.
* Cells that must change for m=299: the 159 pointer variables, initial DEST (29265->27855),
  INCREMENT masks (carry level differs), the 94 table cells (29420->28010), cells 139/142/154
  and the final handoff value (29509->28099).
* Each changed value needs a re-synthesised tmp-based A-load; length differs but opcodes are
  position-independent (denormalised per cell), so lengths may change freely.

## Segmentation result (`seg.py`)
309 tmp-load segments (mean 50 ops, 15,518 of ~27,300 track ops) end with the tail
`<tmp-op @154> o o j o (j|p)@148`.

## Breakthroughs & Solved Items (2026-10-15)
1. **Analytical Trit-by-Trit Constant Generator (BFS NOT NEEDED)**:
   Instead of a combinatorial BFS over 16M states, an analytical trit generator based on
   Module 0 ternary rotation/crazy mechanics (`load_constant_to_a_reg`) was implemented
   and verified. It synthesizes all 215 target constants in 3,370 total operations (mean 15.7 ops/constant),
   with 100% success (215/215).
2. **INCREMENT_BY_9 Carry Mechanics**:
   Evaluated and confirmed for m=299 batches (levels 0, 1, 2, 3 mapped to cells 146, 145, 144, 143).
3. **Late Phase & Cell 142 Trap Solved**:
   Cell 142 values are confirmed arithmetic products of `crazy(C2(DEST), 0)` during carry detection.
   Cell 148 is reset to 44 via `crazy(29492, 29524) = 44`.
   Landing table cells 45..138 are overwritten with 28010 via magic constant 3785 (`crazy(3785, 29524) = 28010`).
   Handoff jump loads A=28099, D=28100, entering loop at c=27668.
4. **Loop Execution Verified**:
   Shifted loop for m=299 verified under high-speed simulator: 66,199,831 steps, emitting
   exactly 56,993 bytes (diff -u = 0 bytes vs wrapped clean_m299).

## Current Status & Next Milestone
- `[CURRENT]`: Loop logic, arithmetic constants, candidate assembler, and analytical constant generator.
- `[NOT_DEMONSTRATED]`: Integrated standalone execution starting from raw disk image without pre-initialized memory.

Files here: `lt.py`, `seg.py`, `mb_ref.c`, `mb_ref`, `synthesize_m299_quine.py`, `m299_candidate_56993b.mal`, `final_phase_explanation.md`.

## Session 2026-10-16 — m-descent results [CURRENT, mb_ref-verified]

New record: **m=284, `candidate_m284_54134b.mal`, 54,134 bytes** (mb_ref 0-byte diff PASS).
Also verified this session: m=293 (55,850 B), m=308 regression (58,709 B). Lutter = 59,852 B.
`m299_candidate_56993b.mal` re-verified as INVALID: mb_ref emits 0 bytes, exit 0.

### Tooling: `synthesize_v2.py` (instrumented copy of `synthesize_clean.py`)
- PHASE opcode breakdown per phase + LENS (synth/ret lengths); summary before handoff.
- Dijkstra edge 6 = `'*jopjo'` (x -> crazy(rot x, rot x), 6 chars, verified pure under all
  entry A). REJECTED as edges: `'pjo'` and `'pjo*jo'` — they depend on entry A (impure
  mid-run; broke m=308 assert).
- `get_return_code` minimized over cand window (from_addr, +40), cost = walk + route.
- Increment macros searched AT RUNTIME at the inc point with the REAL A: hard-4 first, then
  capped BFS (depth<=24, 150k nodes, ops {o,j,*,p}). No BFS macro was ever found in a
  successful run.
- Landing increments use the same runtime search.

### Findings
- **Prefix validity rule: m ≡ 2 (mod 3)** in [161,314]. Cause: cells >= 2C take the native
  crazy init in the real machine; Lutter's prefix reads them (e.g. mem[59033] must be 49;
  L=2C start shifts the chain). Ladder: {..., 239, 242, 245, 248, 251, 254, 257, ..., 284,
  287, 290, 293, 296, 299, 302, 305, 308, 311, 314}.
- **Stream size (synthesized opcodes) is quasi-random in m** (target layout luck):
  observed 24,024 .. 26,895 (7-edge v2). With the 26-edge graph (2026-10-16) m=284 drew
  22,630 (g_synth 8,438, mean 39.2) and PASSED with margin 2,126. Capacity rule:
  preamble c <= 94m - 3; pre-jump includes 1,473-op prefix.
- Passing draws: m=308 (24,846), m=293 (24,387), m=284 (22,630 ext v2; margin 2,126),
  m=287 (fits; file 54,706 B).
- **2026-10-16 triage (26-edge graph), pre_jump vs limit 94m-1,946**: 287 PASS (<=25,032);
  278: 26,504>24,186; 275: 26,454>23,904; 269: 26,498>23,343; 263: 26,618>22,776;
  260: 26,623>22,494; 254: 26,592>21,930; 251: 26,532>21,648; 248: 25,597>21,366.
  Typical (unlucky) chains draw ~26.5k; 284/287 ~24-25k. **m<284 blocked by stream floor.**
- Inc-macro dead values (no hard-4, no BFS<=24 from that state, even with real A):
  27,699 (m=296), 26,235 (m=281), 25,506 (m=272, confirmed 2026-10-16), 24,780 (m=266),
  22,596 (m=242), 24,051 (m=257). **m=281 SOLVED 2026-10-17 with the constructive composite
  below**; the rest are candidates for the same fix.
- **Constructive composite inc (2026-10-17, `do_composite_inc` in `synthesize_v2.py`)**: on a
  dead value the runtime fallback now performs TWO guaranteed seed-style writes `V -> W -> V+9`
  (W = V with the carry-run trits 2..j set to 1, plus 23 random variants over the V==1 digits;
  X1/X2 from `solve_crazy_first`, staged via `'ojoooooo'` + Dijkstra + the `'ooojopj'` dance).
  Fires only where the old code raised RuntimeError. Verified algebra offline
  (`crazy(X1,V)==W`, `crazy(X2,W)==T`) and live (m=281: V=26235, W=3276, X1=39364, X2=3280;
  68 ops total, single use). Note: the hard macros can still succeed on dead values mid-run
  when the live module re-finds cell 148 (m=281 iterations 2/5/11/14 passed silently).
- Capacity overflows (stream > 94m-1,943): 299, 278, 275, 269, 263, 260, 254, 251, 248,
  245, 239 (290/287 fit in the file-size sense only if a 94m-3 pre-jump fits; 287 did).
- **EDGES[19..21] misalignment bug (2026-10-16, fixed)**: macro_code[19..21]
  ('ooj*opopjo*jo', '*oj*opopjo*jo', '*ojo*popjo*jo') had tables (cr_19682_2, cr_39365_1,
  cr_39365_2) instead of (cr_39365_1, cr_39365_2, cr_19682_2). Symptom: dijkstra expected
  X=6557 while runtime produced 52482 (mem[154] post-chain). Diagnosis: char-sim of the true
  chain from the real pre-state (d=154, a=59048, mem[154]=59042) reproduces 52482 == EDGES
  table composition; individual macros verified pure over all 59,049 x under both 152 bases
  (59046/59047). Fix = reorder those 3 EDGES entries; rerun m=284 -> PASS, stream 24,024->22,630.
- `generate_constant` ("analytical trit generator") measured at mean 19.3 ops = 112.2 chars/
  constant vs dijkstra 65.9-72.9: **not a size win**; the 3,370-op claim does not translate.
- Sub-20KB is impossible with this architecture: write path (~13x215=2,795) + landing (~3,900)
  + prefix/loop (1,940) > 7,460 budget (m=100). Requires engine redesign.

### Artifacts (sha256)
- `candidate_m281_53562b.mal`  96b670b825372a0f41fa3b574d47457f92654b76411e5d5be4c438003087610e
  (2026-10-17: first sub-m284 quine, 53,562 B; stream 24,094, margin 380 under capacity
  25,947; composite inc x1; dual-engine verified)
- `candidate_m284_54134b.mal`  1808fd4d862a274abc6b9f7b8965d1eee65fc11aa2424c23a8077040876b483c
  (ext-v2 rebuild 2026-10-16, stream 22,630, mb_ref 0-byte diff; supersedes 391b5f7a...;
  previous record since 2026-10-17)
- `candidate_m287_54706b.mal`  3da997b9e559230d43acf828188269d441afc03d773e71a83f49ae7e9d663efb
- `candidate_m293_55850b.mal`  1719515d85fa2d5dfc0c36cdcc935eefd363fca0a435b2588ef36a1509b1b2ea
- `candidate_m308_58709b.mal`  67628cf1cd8befe907c39aac6476d31927499f0421013c34195891f2ec4ca071
- `synthesize_v2.py`           56088d2c49f1c8311db563a918beeffe0d4323a43dd490991e3b2d155c16056b
  (26-edge graph + SYNTHFAIL/OVERFLOW diagnostics + `do_composite_inc` fallback, 2026-10-17)

### Next steps (ranked, updated 2026-10-17)
1. **Chain-level X selection (DP/beam)**: per-cell X=solve_crazy_first(v,v+9) is chosen greedily
   from the current position; the choice changes the next cell's start value (chain). Unlucky
   chains pay +90/group. Optimizing the 215-long chain (cached dijkstra pair costs) could cut
   hundreds to ~2,000 ops -> makes m=278 (-2,321) and maybe m=275 (-2,550) fit.
   Chain-DP measured 2026-10-17 (savings): 284:320, 278:108, 275:126, 269:146, 263:169,
   260:171, 254:115, 251:151 — greedy already near-optimal; NOT sufficient alone for m<=278.
2. Phase-2 edges (len-14 classes: cf 59045/44/43, 29412, 112, 3160, 26364, 3187, 26337; more
   cf_rot) + macro enumeration maxlen 15-16: expected -200..-500 in g_synth.
3. ~~Cell-148 reset-write fallback~~ **DONE 2026-10-17** as the constructive composite
   (`do_composite_inc`); unlocked m=281. TODO: try the remaining inc-dead m (296, 272, 266,
   257, 242) with the composite synth.
4. Walk-cost attack: g_write+g_clear+land_clear+land_write+land_reload ~ 10.7k ops (44% of
   preamble) are 'o'*(k-1) walks; jump-routing for write positioning is the next big redesign.
5. c-robust predictive write (old_p at p-time) for deeper descent.

