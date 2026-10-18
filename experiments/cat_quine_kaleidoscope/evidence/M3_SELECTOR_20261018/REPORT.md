# M3 selector — dual-path Q/C candidate (2026-10-18)

Environment: Linux (Ubuntu 24.04), BolgeForge worktree (repo root), `tools/trace_loop` (gcc -O2).

Candidate: `candidate_selector_m281.mal` (53,562 B), sha256 `7cab1285…`, derived from
`artifacts/candidate_m281_53562b.mal` (sha256 `96b670b8…`) by `tools/selector_dev.py build`.
Params: y=124, m=64, zQ=89, zC=122, S=187, LQ=44, LC=40, h1=35, H=34, Z=36;
plants `{34:35, 36:45, 38:124, 40:122, 44:89}`; 22 effective byte edits, each mirrored
at p+26414 (keeps the file's A==B self-consistency). Search found 1816 candidates over
8 valid y; only rank [0] was dry-run and built.

## Exact commands + raw results

Q path:

    printf 'Q' | ./tools/trace_loop work/candidate_selector_m281.mal -f 25976 -o work/out_q_selector.bin

    steps=62239932 halt=v prints=53562 out_bytes=53562 anomalies=0
    trigger: step=25532 c=25976 d=26409 a=26407 (prints=53562)
    stdin reads: preamble=1 loop=0
    SANITY out==src: 1 (byte-for-byte, 53562 bytes)
    loop phase: 103 cells, 62214400 events (identical to original run)

`out_q_selector.bin` sha256 == candidate sha256 (output is the source file itself).

C path:

    printf 'C' | ./tools/trace_loop work/candidate_selector_m281.mal -f 25976 -o work/out_c_selector.bin

    steps=25533 halt=v prints=0 out_bytes=0 anomalies=0
    stdin reads: preamble=1 loop=0
    executed cell 36 (=Z, planted 'v') exactly once; loop phase 0 events

Python dry-runs (`selector_dev.py try`): Q entry (25976, 26409, 26407) at step 25532,
ip=1; memory diffs vs original loop entry all inside the allowed set (script range
25560..25646, plants, mirrors). C halt c=36 step 25533 ip=1 prints=0.

## Claims

| claim | status |
|---|---|
| Q path: byte-exact quine on Classic 3^10 VM with real stdin 'Q' | DEMONSTRATED |
| Q total steps == 62,239,868 + m (m=64 → 62,239,932) | DEMONSTRATED |
| Q loop phase identical to original (62,214,400 events) | DEMONSTRATED |
| C path: first-byte 'C' halts at engineered cell Z=36, zero output, no loop | DEMONSTRATED |
| stdin accounting: preamble=1, loop=0 on both paths | DEMONSTRATED |
| C path payload echo (K2) | NOT_DEMONSTRATED (C halts; echo is the K2 stage) |
| remaining 1815 search candidates end-to-end | NOT_DEMONSTRATED (only index [0] built/run) |

Scope: this candidate, this VM (Classic 3^10), these two single-byte inputs. No claim
about other malbolge interpreters, multi-byte stdin, or the K2 payload mode.

## Files

- `candidate_selector_m281.mal` — built candidate (copy of work/ artifact)
- `out_q_selector.bin` — Q output (byte-exact copy of candidate)
- `out_c_selector.bin` — C output (empty)
- `run_q_report.txt`, `run_q_stderr.txt`, `run_c_report.txt`, `run_c_stderr.txt` — trace_loop raw reports
- `search_report.txt`, `dryrun_report.txt` — selector_dev.py search/try outputs
- `sha256sums.txt` — hashes of the above
