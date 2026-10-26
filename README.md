# BolgeForge

A synthesizer and research laboratory for Classic Malbolge. The verified core contains byte-exact quines, the historical reference corpus, four rebuilt compressed benchmarks, a smaller compact Cat (7,690 cells) and an independent 120-cell Truth Machine. Experimental programs are preserved separately from certification claims.

```bash
make test
make test-rebuild
```

Owner's instructions in Spanish: [GUIA.md](GUIA.md).

## Verified milestones and limits

| Result | Status and scope |
|---|---|
| Quine m=281, 53,562 file bytes | Exact self-reproduction under independent strict execution. Full synthesis reproduced SHA-256 `96b670b825372a0f41fa3b574d47457f92654b76411e5d5be4c438003087610e` in the audit. Smallest of the five committed quines and the smallest verified in the audited corpus; worldwide supremacy and historical primacy are **RETIRED** (universal/historical negatives outside this evidence scope). |
| Five committed quines | Strict loading, HALT and byte-exact self-reproduction are required for every file. |
| Eight historical reference programs | Checked against explicit output expectations and exact self-reproduction for the historical quines. |
| Four compressed benchmarks | Strict execution and reference parity on the documented vectors. Rebuilding must reproduce the committed bytes. This is finite testing, not a proof for every input. |
| Compact streaming Cat, 7,690 cells | **DEMONSTRATED** by `artifacts/cat_compact.mal` (k=18 plan, compact boot): 564 cells fewer than the compressed Cat (6.8%) and 1,692 fewer than the 9,382-cell reference (18.0%), with the reference handoff state reproduced 124/124. Exact-output battery through 64 KiB binary under both `mb_ref` and the independent Olmstead mirror. Finite testing, not a proof for every input. The plan is 7,199 preamble operations against the 7,213 k=18 budget: the compact boot removed 132 never-used BOOT operations (the mem[89] odometer constant, a shorter rotor path, a sp-48 rework, a mem[93] fuse), leaving the write phase untouched. The measured frontier below 7,690 is k=19 at −81 operations (budget 7,118, current floor 7,199), so a streaming Cat below 7,690 cells remains **NOT_DEMONSTRATED**. |
| MicroCat, 3,380 bytes | **REFUTED as a Classic artifact.** The historical permissive VM echoes at most three input bytes; `ABCD` becomes `ABC`. The streaming-Cat capability is **DEMONSTRATED** separately by `cat_compressed.mal` (64 KiB binary stream, strict HALT). |
| Truth Machine, 90 bytes | **DEMONSTRATED** by a strict-valid reproduction (`artifacts/truth_machine_classic_90b.mal`, provenance in `docs/provenance/truth_machine_90b.json`): input `0` prints `0` and halts; input `1` repeats the full VM state after 408 instructions and emits 17 bytes per cycle, proving an infinite `1` stream. Historical primacy is **RETIRED**. The old 103-byte artifact remains rejected by the strict loader. |
| Independent Truth Machine, 120 cells | **DEMONSTRATED** by `docs/evidence/2026-10-25-truth-machine-v5/tm_independent_v5.mal` (2026-10-25): independent synthesis with its own kernel geometry, entry, branch and runtime installer; no byte, cell or constant is copied from the 90-byte reproduction, though it reuses the cycle mechanism decoded in the M1/Phase 2 research, which is common to this kernel family. Strict loader **ACCEPT** (0 invalid cells); input `0` prints one `0` and halts at step 27; input `1` repeats the full VM state after 408 instructions with 17 bytes per cycle. `tools/prove_truth_machine.py` returns verdict `DEMONSTRATED` with six passing checks, and the recompiled `oracle/mb_ref.c` agrees on both branches. Historical primacy is **RETIRED**. |
| FizzBuzz, loader-valid reference | **DEMONSTRATED** with the preserved [angel_p_57 conversion](https://github.com/angel-p57/malbolge/tree/b2d278d36e65d66574d435d4cfeb1560b79ed593) (`docs/audits/2026-10-20-e2e/angel_fizzbuzz_converted.mal`): empty stdin, 413 bytes, 100 exact lines, strict HALT. It performs 109 EOF reads. Zero-read behaviour, divisibility computed inside the VM, and historical primacy are **RETIRED**. The old 4,517-byte artifact remains rejected by the strict loader. |
| Q/C selector and other Cat candidates | **RETIRED as a published claim.** The M3 candidate is rejected by strict loading; its historical evidence is retained with the original scope and corrections. The contract's CAT payload echo remains **OPEN** research and is not claimed. |

The alleged EOF defect in the included historical `cat.mal` was refuted: that file terminates cleanly without emitting an extra byte. Mathematical identities in research notes do not establish correctness of complete programs.

After the 2026-10-20 closure pass, every item in this README, the roadmap and the claims ledger has a terminal status: DEMONSTRATED with evidence, REFUTED, RETIRED (withdrawn, neither asserted nor denied), or OPEN and explicitly unclaimed. The ledger preserves the audit's historical NOT_DEMONSTRATED findings in its audit-result column; historical research and experiment artifacts keep their original labels as evidence. The full mapping is in [the claims ledger](docs/CLAIMS.md); raw evidence is in [the closure evidence](docs/evidence/2026-10-20-closures/). Three items were added after that pass with their own dated evidence: the 7,972-cell compact Cat (2026-10-24, superseded the next day), the independent 120-cell Truth Machine (2026-10-25) and the 7,596-cell k=19 compact Cat (2026-10-25, which replaces the published artifact). The frontier attacks recorded along the way (k=18 gap measurement, window tiling, chain sweeps, the m1 `*jo` transfer) are refutations with dated evidence; the superseded 7,972 bytes remain rebuildable from git history.

## Compression

| Benchmark | Original cells | Compressed cells / file bytes | Cells saved |
|---|---:|---:|---:|
| Cat | 9,382 | 8,254 | 1,128 |
| Digital Root | 32,136 | 26,308 | 5,828 |
| Adder | 56,476 | 44,914 | 11,562 |
| 99 Bottles | 22,561 | 21,809 | 752 |
| Total | 120,555 | 101,285 | 19,270 (15.98%) |

These savings compare non-whitespace cells. Formatted reference file bytes are a different measure. Digital Root and Adder were repaired using the actual linear handoffs at 31,802 and 55,802. Their corrected hashes and preserved previous artifacts are recorded in [the repair report](docs/repairs/2026-10-20/REPORT.md).

A separate, smaller Cat variant also exists: `artifacts/cat_compact.mal` streams the same inputs exactly in **7,596 cells** (564 fewer than the compressed Cat, 1,692 fewer than the reference), with the reference handoff state reproduced 124/124. It is generated deterministically by `tools/build_compact_cat.py` (k=19 plan, compact boot), certified by `tests/test_compact_cat.py`, and documented in [the compact-cat-k19 evidence](docs/evidence/2026-10-25-cat-k19-frontier/REPORT.md) (the first 7,972-cell build: [compact-cat-k15 evidence](docs/evidence/2026-10-24-compact-cat-k15/REPORT.md)).

Tests cover binary Cat streams through 65,536 bytes (including the compact Cat under both `mb_ref` and the independent Olmstead mirror), six Digital Root vectors, 100 Adder pairs with each operand in the author's `0..999` domain, the complete 99 Bottles output, the strict-valid Truth Machine (including its cycle proof), its behavior-preserving 90-byte variant, and the loader-valid FizzBuzz reference. They compare reference and compressed programs and require strict HALT. The generator validates a candidate before publishing it; `--check` never changes published artifacts.

## Oracle and verification

`oracle/mb_ref.c` validates each initial cell against the eight Classic instructions at its actual load address. Whitespace does not occupy a cell. At least two cells are required. Execution preserves the original jump/destination-encryption behavior. A nonprintable program counter is reported as a stall; an invalid encryption word is reported instead of indexing outside the table. These diagnostic exits are documented host safeguards.

```bash
make                         # Build mb_ref
make test                    # Oracle regressions, reference corpus, compressed outputs, quines, independent mirror
make test-rebuild            # Rebuild four compressed files, verify semantics and committed bytes
python3 tools/build_compact_cat.py --check   # Rebuild the compact Cat (k=19) and compare published bytes
python3 synthesize.py 281     # Regenerate m=281; approximately 13 minutes in the audit
python3 tools/resynthesize.py all --output-dir /tmp/bolgeforge-new-build
```

The default VM budget is 100,000,000 iterations; pass another unsigned decimal budget as the second argument. Exit 0 means HALT and successful output flushing; exit 1 means invalid source/arguments or program-file I/O failure; exit 2 means budget exhausted; exit 3 means execution stalled or encryption was undefined; exit 4 means stdin/stdout failure. A finite output prefix never proves infinite behavior.

`make test` does not write artifacts (it rebuilds the compact Cat in memory to check determinism). It fails on missing expected artifacts, any earlier quine failure, an output mismatch or a non-HALT exit. Loader rejection controls protect against accidentally certifying the experimental artifacts. Legacy `test-tm` and `test-fizzbuzz` challenges remain outside certification and currently fail on their invalid sources.

## Evidence and research

- [Original E2E audit](docs/audits/2026-10-20-e2e/REPORT.md): immutable evidence for commit `2fe8e80`, including independent strict execution and the complete quine synthesis.
- [Repair report](docs/repairs/2026-10-20/REPORT.md): changes, current checks, hashes and remaining limits.
- [Independent Truth Machine evidence](docs/evidence/2026-10-25-truth-machine-v5/REPORT.md): 120-cell independent synthesis, prover output, oracle transcript and hashes.
- [Compact Cat k=18 evidence](docs/evidence/2026-10-25-compact-cat-k18/REPORT.md): the 7,690-cell build, independent verification battery (control run, boot-state diff, odometer usage, post-handoff trace) and integration record.
- [Cat frontier attacks](docs/evidence/2026-10-25-cat-chain-sweeps/REPORT.md): k=18 plan at 7,331/7,213, window-tiling DP, multi-target chain sweeps and the m1 `*jo` register transfer refuted — the refutation chain that located the real lever (the BOOT phase).
- [Roadmap](docs/ROADMAP.md): completed work and open research.
- [Historical Cat research](docs/CAT_ANALYSIS.md) and [corpus telemetry](docs/CORPUS_AUDIT.md): dated research, subject to their correction notices.

The comparison quine of 59,852 file bytes is Lutter's formatted 2015 reference ([malbolge.org](https://malbolge.org/quine.html)); the 2012 source has 59,032 cells/bytes without that formatting. Comparing m=281 to the formatted file saves 6,290 file bytes; comparing cells saves 6,204. On 2026-10-20 the downloaded `quine.mal` was 59,852 bytes / 820 lines (SHA-256 `dca8476f8b70c8462c32f661f63c5f8b1ad6c33946b3c7a9a35186c824117d98`), byte-identical to the committed reference; angel_p_57's `sample/fizzbuzz.txt` was 413 bytes (SHA-256 `f039dc221ad122dda8b7226ad5bc68b8654e9e3a42dcea2b37554cd6f91b56af`). Machine-readable details are in [external_sources.json](docs/evidence/2026-10-20-closures/external_sources.json).

## License

MIT; see [LICENSE](LICENSE). Historical reference programs retain their attribution. The 90-byte Truth Machine reproduction is CC BY-SA 4.0, as recorded in `docs/provenance/truth_machine_90b.json`. No record or novelty claim follows from a green test alone.
