# CONTRACT — CAT-QUINE Kaleidoscope (Classic Malbolge 3^10)

**Status:** FROZEN v0.1 (gate M0) · 2026-10-18 · author: `opencode_maintainer_1792266511`
**Compose:** `COMPOSE_GEMINI_CAT_QUINE_KALEIDOSCOPE_2026-10-18.md` (user-owned, in `~/Descargas`)
**Scope:** Malbolge **Classic** (10 trits, 59,049 cells) only. Not Unshackled (3^19).

---

## 1. Definitions

- **P** — a single `.mal` source file. `source_bytes(P)` = the exact file bytes as stored
  (including spaces/newlines; no normalization of any kind).
- **VM** — Classic Malbolge with the semantics implemented in `oracle/mb_ref.c`
  (Olmstead specification), as observed in M0 (frozen here):
  - Load: read file; skip `isspace` bytes; require bytes 33..126; cells 0..n-1 = source
    printable bytes; pad rest with `op(mem[i-1], mem[i-2])`.
  - Decode: `xlat1[(mem[c]-33+c) % 94]`.
  - Invalid instruction at `c`: `c++`, `d++`, **no** self-encryption, `a` unchanged.
  - `<` outputs `a & 255` (one byte). `/` reads one stdin byte into `a`; **EOF ⇒ a = 59048**.
  - `v` halts immediately (no tail step). All other valid instructions end with
    `mem[c] = xlat2[mem[c]-33]; c++; d++` (mod 59,049).
- **Selector** — first stdin byte. `'Q'` = 0x51 = 81, `'C'` = 0x43 = 67.
- **HALT** — real `v` execution, distinguished from step-cap exhaustion. A run that hits
  `max_steps` is `NOT HALT` (F09). mb_ref does not currently distinguish the two in its
  output channel; M0 uses time-bounded runs + truncation controls; an observability runner
  is scheduled (trials must record which runner produced evidence).

## 2. Protocol v1 (PRIMARY — EOF-terminated)

| Mode | stdin | Required stdout | After output |
|---|---|---|---|
| QUINE | `0x51` then EOF | `source_bytes(P)` **byte-for-byte** | HALT |
| CAT | `0x43` then payload (any bytes 0x00..0xFF) then EOF | payload **byte-for-byte** | HALT |

- EOF-termination chosen over the compose v0 4-byte length framing: in this VM EOF is
  unambiguous (`/` ⇒ 59048; payload bytes are ≤ 255), needs no ternary length parse, and
  was validated empirically in M0 with 0x00/0xFF payloads. The length-framed variant of
  compose §3 remains an OPTIONAL secondary encoding if ever needed.
- Undefined (never claimed): first byte ∉ {Q,C}; extra bytes after `Q`; processes that
  never terminate; payloads beyond the max tested per run report.
- **No host semantics**: the host may only assemble the same P, feed stdin, run the VM and
  compare bytes. Printing P from outside the VM, per-mode regeneration/patching of P, or
  two different executables are automatic FAILs (compose §4).

## 3. Verified synthesis primitives (M0)

- **Selector primitive (single `p`)** — with `a = selector` from `/`, and `mem[d] = 29524`
  (a load-time constant of our layout): `p` computes
  `op(sel, 29524)` = **29443** for `Q`, **29538** for `C` (distinct). The result is written
  back to that cell by `p` itself, so an `i` through it jumps to
  `c = 29444` (QUINE branch) or `c = 29539` (CAT branch). Cost ≈ route + 1 `p` + 1 `i`.
  (Alternative, via `op(29524, sel)` = 0 for `Q`, 54 for `C`, needs the selector in
  memory; noted, not needed.)
- **EOF detector (reproduced independently — origin: `antigravity_microcat` CAT_ANALYSIS)**
  — `op(op(59048, x), 29524) == 0 ⟺ x == 59048`; also valid in swapped order. Verified
  over all 257 inputs (0..255, 59048) with the mb_ref.`op` table.
- **Mutation rule (compose H3)** — any scratch/mutation used by the selector or CAT branch
  SHOULD live in the pad region (cells ≥ loaded length) or be deterministic and accounted
  for by the quine print logic. Branch entries placed inside the source region may be
  executed (normal self-encryption), but every non-uniform write must be part of the
  deterministic per-mode history the QUINE branch can reproduce.

## 4. Oracle matrix (independence)

- **Primary:** `oracle/mb_ref.c` (C, Olmstead). Source sha256 and binary recorded per run.
- **STATUS: SINGLE-ENGINE VERIFIED.** A genuinely independent second Classic engine has NOT
  been validated yet (compose §1.4: study real parity first; `epochal` is not fixed
  Classic). Until then no cross-implementation claim.
- **K0 fixture engine:** the historical `reference/malbolge_org/cat.mal` (external artifact
  by M. Lutter, hash-frozen) is a reference *program*, not an oracle; it shares no semantics
  implementation with mb_ref.

## 5. Gates

- **K0 (integration tube):** historical CAT round-trips `source_bytes(Q)` ⇒ `DEMONSTRATED`
  (M0, both historical quines byte-exact) — but this is NOT K2 and never labeled as such.
- **K1:** a BolgeForge-synthesized CAT under §2 (one artifact, multiple payloads, mutation
  tests) — pending.
- **K2:** single image P satisfying both rows of §2 — pending (M3).

## 6. Evidence conventions

- Raw stdin/stdout/stderr files, SHA-256 of P/input/output, exit status, wall time, step
  caps, engine name+version, OS; unique per-run filenames under
  `experiments/cat_quine_kaleidoscope/evidence/`.
- `SKIP ≠ PASS`; inapplicable tests ⇒ `NOT_APPLICABLE` + reason. Byte-compare is strict
  (no newline normalization anywhere).
