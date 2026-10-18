# CAT-QUINE KALEIDOSCOPE — RUN REPORT (M0)

```
REPO / PATH / BRANCH / HEAD / DIRTY: BolgeForge (repo root) / master / 103b2eb (atop 5 local unpushed commits by antigravity_microcat) / dirty (this dir, untracked)
MILESTONE: M0 (baseline + contract + fixtures)  [M1 partially pre-run: K0]
STATUS: K0 DEMONSTRATED (fixture tube only) · K1 NOT_DEMONSTRATED · K2 NOT_DEMONSTRATED · selector primitive OBSERVED (algebraic, not yet executed in a VM)
MACHINE: Classic 3^10 fixed (yes) — 59,049 cells, mb_ref.c Olmstead semantics
ARTIFACT P: none yet (K2 pending) — references frozen: cat.mal ce04a6f2 (9,503 B) · quine-2012.mal 419e274e (59,032 B) · quine.mal dca8476f (59,852 B) · adder f7a23ea3 · digital_root d23023b7
PROTOCOL: CONTRACT_CAT_QUINE.md v0.1 (EOF-terminated; QUINE='Q'+EOF; CAT='C'+payload+EOF; undefined outside)
IMPLEMENTATION BOUNDARY: host only assembled commands, fed stdin, compared bytes (cmp/sha256sum). All program behavior from the VM.
CHANGES: new files only — experiments/cat_quine_kaleidoscope/{CONTRACT_CAT_QUINE.md,RUN_REPORT_M0.md,evidence/M0_20261018/**}
EXECUTED: see evidence/M0_20261018/commands.txt (make; fixture runs; truncation control; selector/EOF algebra check)
TEST MATRIX (M0 subset of compose F-battery):
  F02/F03-style: cat 'A' -> 'A'; 'ABC\n' -> 'ABC\n' : PASS (same artifact, distinct payloads)
  F04-style: cat empty -> empty : PASS
  F05-style: cat 00 ff 0a -> 00 ff 0a : PASS (byte-exact)
  K0: cat < quine-2012.mal -> 419e274e byte-exact, exit 0, 72 ms : PASS
  K0: cat < quine.mal      -> dca8476f byte-exact, exit 0 : PASS
  F09-style control: max_steps=500000 on 59,032 B payload -> truncated 1,206 B : OBSERVED (full run necessarily consumed more; HALT is inferred from 72 ms full completion, observability runner pending)
  F01/F06/F07/F08/F10/F11/F12: NOT_APPLICABLE yet (require the K2 artifact / second engine)
EVIDENCE: experiments/cat_quine_kaleidoscope/evidence/M0_20261018/ (stdin/stdout pairs, reference_hashes.txt, commands.txt)
INDEPENDENT ORACLES: mb_ref.c only (SINGLE-ENGINE). Second Classic engine not yet validated.
CLAIMS NOT PROVEN: no dual image exists; no BolgeForge CAT (K1); K0 does NOT imply K2; selector primitive not yet executed inside a VM; HALT not yet instrumented.
ROOT CAUSES / COUNTEREXAMPLES: EOF-terminated protocol validated because payloads include 0x00/0xFF/0x0A without ambiguity; selector algebra `op('Q',29524)=29443 ≠ op('C',29524)=29538` gives two distinct jump targets from one `p`+`i`.
NEXT SMALLEST EXPERIMENT: M2 — decide K1 CAT basis (adopt/verify micro-cat vs new synth under this contract), then M3 selector+layout sketch (space budget: source region 0..len(P)-1, scratch ≥ len(P); record plan with branch entry cells 29444/29539 or a re-searched constant with smaller landings).
ROLLBACK: delete experiments/cat_quine_kaleidoscope/** (new files only; no tracked file touched).
```
