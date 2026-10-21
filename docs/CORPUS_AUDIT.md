> **Historical corpus telemetry — correction, 2026-10-20.** The tables below preserve the 2026-10-18 report and its original hashes. CURRENT and 100% labels below are historical claims, not universal conformance proofs. The audit found that Digital Root and Adder did not regenerate from that source. The repaired generator uses handoffs 31802 and 55802; current compressed artifacts have new hashes, documented in the repair report. Previous artifacts are preserved there. The M3 selector fails strict loading and is not a demonstrated Classic program.
> See [the E2E audit](audits/2026-10-20-e2e/REPORT.md) and [repair report](repairs/2026-10-20/REPORT.md) for evidence and current scope.

# BolgeForge Corpus Telemetry & Structural Audit

**Date:** 2026-10-18  
**Scope:** Complete canonical reference suite in `reference/malbolge_org/` (8 programs)  
**Verification Oracle:** `oracle/mb_ref.c` + `tools/audit_bloat.py` (Olmstead Classic Malbolge, 59,049 ternary cells, zero hardcoded estimates)

---

## 1. Executive Summary

We performed an instruction-by-instruction dynamic execution audit across all 8 canonical programs from [malbolge.org](https://malbolge.org/) to separate **initialization preamble** from **post-I/O algorithmic execution** (`[CURRENT]` verified on disk).

Key findings:
1. **Unrolled HeLL/LAL Programs (`digital_root.mal`, `adder.mal`, `99_bottles.mal`, `cat.mal`):** **96.0% to 99.0%** of the program opcodes form a single linear initialization stream (`c = 99 .. Linear End`) that populates memory words via `*` and `p` before jumping into a compact trampoline loop (`36` to `106` distinct `c` cells executed post-I/O).
2. **Runtime Table-Generator Loop (`rot13.mal`, Sakai & Iizawa 2006):** Exits its linear stream early (`c = 738`) and executes **10,827,097 steps** of looped initialization that modifies **7,489 distinct memory cells** (`7,145` inside `< 33,031` and `344` in `>= 33,031`) before reading its first input character (`/` at `c = 611, d = 229`).
3. **Rolled Module-0 Quines (`quine.mal`, `quine-2012.mal`, Lutter):** Use a rolled Module-0 loop (`24,960`–`28,315` preamble steps modifying `281`–`333` cells via `j`-driven macros). BolgeForge's verified `synthesize.py` compressed this family to **`m = 281` (53,562 B)** (`[DEMONSTRATED]`, 0-byte diff in C oracle).

---

## 2. Exact Telemetry Matrix (`[CURRENT]`)

Reproducible in `< 2s` via `python3 tools/audit_bloat.py` (`make audit`):

| Program | File Bytes | Program Opcodes ($n$) | Linear Preamble End ($c$ / % of $n$) | First I/O Step & Op (`@step (op)`) | First I/O State ($c, d, a$) | Preamble Modified Cells (`Total = Low + High`) | Post-I/O Executed $C$ Cells (`Total = Low + High`) | Total Steps to `v` HALT |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| **`99_bottles.mal`** | 22,807 B | 22,561 | `22,044` (**97.7%**) | `@23,868 (<)` | `c=22303, d=29468, a=57` | **444** (`26` + `418`) | **68** (`42` + `26`) | 13,802,605 |
| **`adder.mal`** | 57,283 B | 56,476 | `55,802` (**98.8%**) | `@55,705 (/)` | `c=56255, d=58949, a=29524` | **809** (`38` + `771`) | **106** (`18` + `88`) | 286,924 |
| **`cat.mal`** | 9,503 B | 9,382 | `9,003` (**96.0%**) | `@8,992 (/)` | `c=9067, d=58999, a=29524` | **161** (`38` + `123`) | **36** (`22` + `14`) | 11,709 *(on `"Hello\n"`)* |
| **`digital_root.mal`** | 32,596 B | 32,136 | `31,802` (**99.0%**) | `@31,705 (/)` | `c=32097, d=58969, a=29524` | **479** (`38` + `441`) | **70** (`12` + `58`) | 262,039 *(on `"12345\n"`)* |
| **`hello_world.mal`** | 89 B | 88 | `40` (**45.5%**) | `@3 (<)` | `c=3, d=3, a=72` | **2** (`2` + `0`) | **45** (`45` + `0`) | 47 |
| **`quine-2012.mal`** | 59,032 B | 59,032 | `99` (**0.2%**) | `@24,960 (<)` | `c=29357, d=59044, a=39` | **281** (`277` + `4`) | **97** (`95` + `2`) | 69,031,647 |
| **`quine.mal`** | 59,852 B | 59,032 | `99` (**0.2%**) | `@28,315 (<)` | `c=29357, d=59044, a=39` | **333** (`329` + `4`) | **103** (`101` + `2`) | 69,547,436 |
| **`rot13.mal`** | 33,383 B | 33,031 | `738` (**2.2%**) | `@10,827,097 (/)` | `c=611, d=229, a=29524` | **7,489** (`7,145` + `344`) | **84** (`39` + `45`) | 11,340,927 *(on `"Hello\n"`)* |

> **Note on `Low` vs `High` cells:** `Low` denotes cells at addresses `< n` (inside the loaded program image); `High` denotes cells at addresses `>= n` (in the `crazy`-filled tail `n .. 59,048`). Notice that `first_io_c` sits *inside* the low-memory trampoline table (e.g., in `cat.mal`, `v` HALT is at `c = 9,025` and a `j, i` trampoline is at `9,049..9,050`, before `/` at `c = 9,067`).

---

## 3. Architectural Autopsy of `99_bottles.mal` (Hisashi Iizawa, 2005)

### A. The Immortal Portal at `c = 0` (`[DEMONSTRATED]`)
Cell `c = 0` (`mem[0] = 98 = 'b'`, which decodes to `i` at `c = 0`) is executed **42,889 times** during the 99-verse run without ever being corrupted by `xlat2`.  
**Why:** In Ben Olmstead's specification (`oracle/mb_ref.c`), instruction `i` sets `c = mem[d]` **before** applying `mem[c] = xlat2[mem[c] - 33]`. Consequently, `i` encrypts the *destination* cell `mem[new_c]` (just before `c` increments to `new_c + 1`, where `mem[new_c]` is a 2-cycle `74 <-> 70` NOP/op pair) and **never encrypts the jump source `c = 0`**.

### B. The `59047 -> 59048 -> 0` Modular Wraparound Bridge (`[DEMONSTRATED]`)
Because Malbolge lacks an instruction to add a small constant to `d` without dereferencing `mem[d]`, Iizawa jumps via `i` to `59047` (13,957 times) or `59048` (42,881 times). Executing NOPs at `59047` and `59048` advances `d` by `+2` or `+1` while `c` wraps around modulo `59,049` directly into the immortal `i` jump portal at `c = 0`.

### C. Ternary-Center (`29524`) Pointer Arithmetic Lock (`[DEMONSTRATED]`)
The lyrics table (`"9876543210 bottles of beer on the wall..."`) is stored in `29649..29826` as an interleaved linked list of ASCII character literals (odd addresses) and continuation pointers (even addresses).  
During the countdown loop, scratchpad cell `29491` dynamically computes verse string addresses (such as `29666`) using `crazy` (`p`) and `rot` (`*`) anchored on the ternary center $29524 = (1111111111)_3$ (the unique non-trivial fixed point of 10-trit rotation, $\text{rot}(29524) \equiv 29524$) and mask $29443 = (1111101111)_3$.
* **Implication for relocation:** Uniformly subtracting a Delta-94 offset ($\Delta_D = 306 \times 94 = 28,764$) from the data table works for the first 1,063 post-handoff steps, then diverges at relative step **1,064** (`tools/compare_sim.c`) when `c = 29396` (`j`) dereferences the dynamically computed address `29666` in cell `29491`. Relocating `99_bottles.mal` to low memory therefore requires re-synthesizing the verse-counter arithmetic constants (`[NOT_DEMONSTRATED]`).

---

## 4. Epistemic Status Summary (`AGENTS.md` §2 & §5)

| Claim / Artifact | Status | Evidence |
|---|---|---|
| **Quine `m = 281` (53,562 B)** | **`[DEMONSTRATED]`** | `artifacts/candidate_m281_53562b.mal` (`sha256: 96b670b8…`), 0-byte diff in `mb_ref`. |
| **Q/C Dual-Path Selector (`m = 281`)** | **`[DEMONSTRATED]`** | `experiments/cat_quine_kaleidoscope/evidence/M3_SELECTOR_20261018/REPORT.md` (`Q` -> 53,562 B quine; `C` -> clean halt at `Z=36`). |
| **8/8 `malbolge.org` Corpus Oracle Suite** | **`[DEMONSTRATED]`** | `make test-corpus` (`test_corpus.py`, 0.45 s, all 8 programs verified in `mb_ref`). |
| **2-Step Ternary EOF Detector Invariant** | **`[DEMONSTRATED — ALGEBRAIC]`** | $\text{crazy}(\text{crazy}(59048, x), 29524) = 0 \iff x = 59048$ across all $x \in \{0..255, 59048\}$ (`tools/microcat.py`). |
| **Universal Preamble Relocation & HeLL Resynthesis** | **`[DEMONSTRATED]`** | Complete canonical suite (`cat`, `digital_root`, `adder`, `99_bottles`) compressed by **-19,270 chars (15.98% overall)** with 100% bit-for-bit `mb_ref` oracle pass (`tools/resynthesize.py`). |

---

## 5. Canonical Benchmark Resynthesis Matrix (`[DEMONSTRATED]`)

Synthesizer: `tools/resynthesize.py` (C-accelerated Dijkstra bucket solver, domino pre-clear, intra-window TSP ordering, $-\Delta = -94k$ tail relocation).

| Benchmark | Original (chars) | Compressed (chars) | Saved (chars) | Reduction (%) | SHA-256 (`artifacts/*_compressed.mal`) | Oracle Status (`mb_ref`) |
|---|---:|---:|---:|---:|---|---|
| **`cat.mal`** | 9,382 | **8,254** | **-1,128** | **12.02%** | `b4ddd5ec59f33c7776bf5b85f51065c836dce9135b36a8a3be7f2c2340e85dda` | **100% PASS** (all ASCII + binary) |
| **`digital_root.mal`** | 32,136 | **26,308** | **-5,828** | **18.14%** | `ca20ffb18598f449e15acf3972e87c566130c29cea9749c29ae08034356b66cb` | **100% PASS** (all decimal vectors) |
| **`adder.mal`** | 56,476 | **44,914** | **-11,562** | **20.47%** | `89af80422fec7257bf537684d847a248acd2aba431795fc302f94b93cbee9e48` | **100% PASS** (differential oracle) |
| **`99_bottles.mal`** | 22,561 | **21,809** | **-752** | **3.33%** | `9710e8c47f8926ff737bfe59508299a2b3db8058ca654dc52feb470360dd73dd` | **100% PASS** (full 11,459B lyrics) |
| **TOTAL** | **120,555** | **101,285** | **-19,270** | **15.98%** | *4/4 canonical targets compressed & verified* | **100% PASS** |
