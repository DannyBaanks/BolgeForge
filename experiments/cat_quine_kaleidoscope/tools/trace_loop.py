#!/usr/bin/env python3
"""trace_loop.py - M3 analysis: simulate a Classic Malbolge program and map its phases.

Ground-truth semantics: oracle/mb_ref.c (the repo's canonical oracle).

Reports:
  - full-run sanity: output vs source bytes (quine check), step count, halt reason
  - executed-cell maps split preamble-phase vs loop-phase (--from-c threshold)
  - memory-write maps (p / * with d) split the same way
  - a step window trace of the loop phase (--from-c, --window)

Usage:
  python3 trace_loop.py <prog.mal> [--from-c 25940] [--window 400]
      [--max-steps 2000000] [--stdin HEX] [--out TRACE.txt]
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from constants import XLAT1, XLAT2, crazy_op


def ranges_of(cnt, extra=None):
    nz = [i for i in range(59049) if cnt[i]]
    out = []
    for i in nz:
        if out and i == out[-1][1] + 1:
            out[-1][1] = i
        else:
            out.append([i, i])
    res = []
    for lo, hi in out:
        tot = sum(cnt[x] for x in range(lo, hi + 1))
        res.append((lo, hi, hi - lo + 1, tot))
    return res


def fmt_ranges(res, label, maxr=40):
    print(f"{label}: {len(res)} range(s)")
    shown = res if len(res) <= maxr else res[:maxr]
    for lo, hi, cells, tot in shown:
        print(f"  [{lo}..{hi}] cells={cells} events={tot}")
    if len(res) > maxr:
        print(f"  ... {len(res) - maxr} more range(s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('prog')
    ap.add_argument('--stdin', default='')
    ap.add_argument('--max-steps', type=int, default=2_000_000)
    ap.add_argument('--from-c', type=int, default=-1)
    ap.add_argument('--window', type=int, default=400)
    ap.add_argument('--out', default='')
    args = ap.parse_args()

    src = Path(args.prog).read_bytes()
    clean = [b for b in src if 33 <= b <= 126]
    n = len(clean)
    mem = [0] * 59049
    mem[:n] = clean
    for i in range(n, 59049):
        mem[i] = crazy_op(mem[i - 1], mem[i - 2])

    stdin = bytes.fromhex(args.stdin) if args.stdin else b''
    xl1 = XLAT1
    xl2 = [ord(ch) for ch in XLAT2]

    a = c = d = 0
    step = 0
    sp = 0
    out = bytearray()
    cnt_pre = [0] * 59049
    cnt_loop = [0] * 59049
    wcnt_all = [0] * 59049
    wcnt_loop = [0] * 59049
    loop_active = 0
    win_start = -1
    entry = None
    trace = []
    halt = 'max_steps'
    n_prints = 0

    while step < args.max_steps:
        v = mem[c]
        if v < 33 or v > 126:
            c = 0 if c == 59048 else c + 1
            d = 0 if d == 59048 else d + 1
            step += 1
            continue
        if args.from_c >= 0 and not loop_active and c >= args.from_c:
            loop_active = 1
            win_start = step
            entry = (step, c, d, a)
        if loop_active:
            cnt_loop[c] += 1
        else:
            cnt_pre[c] += 1
        instr = xl1[(v - 33 + c) % 94]
        inwin = False
        if loop_active and step - win_start < args.window:
            inwin = True
            parts = [f"{step}\tc={c}\td={d}\t{instr}\ta={a}"]
        if instr == 'j':
            d = mem[d]
        elif instr == 'i':
            c = mem[d]
        elif instr == '*':
            old = mem[d]
            mem[d] = old // 3 + (old % 3) * 19683
            a = mem[d]
            wcnt_all[d] += 1
            if loop_active:
                wcnt_loop[d] += 1
            if inwin:
                parts.append(f"* d={d}:{old}->{mem[d]}")
        elif instr == 'p':
            old = mem[d]
            mem[d] = crazy_op(a, old)
            a = mem[d]
            wcnt_all[d] += 1
            if loop_active:
                wcnt_loop[d] += 1
            if inwin:
                parts.append(f"p d={d}:{old}->{mem[d]}")
        elif instr == '<':
            out.append(a & 255)
            n_prints += 1
            if inwin:
                parts.append(f"OUT:{a & 255}")
        elif instr == '/':
            if sp < len(stdin):
                a = stdin[sp]
                sp += 1
            else:
                a = 59048
            if inwin:
                parts.append(f"IN:{a}")
        elif instr == 'v':
            halt = 'v'
            if inwin:
                parts.append("HALT")
            step += 1
            break
        if 33 <= mem[c] <= 126:
            mem[c] = xl2[mem[c] - 33]
        c = 0 if c == 59048 else c + 1
        d = 0 if d == 59048 else d + 1
        step += 1
        if inwin:
            trace.append('\t'.join(parts))

    print(f"file={args.prog}")
    print(f"src_bytes={len(src)} clean={n}")
    print(f"steps={step} halt={halt} prints={n_prints} out_len={len(out)}")
    ok = bytes(out) == src
    print(f"SANITY out==src: {ok}")
    if not ok:
        m = min(len(out), len(src))
        first = next((i for i in range(m) if out[i] != src[i]), m)
        print(f"first diff at {first} (out={len(out)} src={len(src)})")
    if entry:
        print(f"loop threshold c>={args.from_c} first reached at step={entry[0]} "
              f"c={entry[1]} d={entry[2]} a={entry[3]}")
        print(f"loop-phase steps={step - entry[0]}")
    fmt_ranges(ranges_of(cnt_pre), "executed c (preamble phase)")
    fmt_ranges(ranges_of(cnt_loop), "executed c (loop phase)")
    fmt_ranges(ranges_of(wcnt_all), "written d (all phases, p+*)")
    if loop_active:
        fmt_ranges(ranges_of(wcnt_loop), "written d (loop phase)")
    if args.out and trace:
        Path(args.out).write_text('\n'.join(trace) + '\n')
        print(f"trace written: {args.out} ({len(trace)} lines)")
    elif args.out:
        print(f"trace window never triggered; {args.out} not written")


if __name__ == '__main__':
    main()
