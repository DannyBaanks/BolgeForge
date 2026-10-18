#!/usr/bin/env python3
"""selector_dev.py - M3 Q/C selector development harness (v2).

EXACT Classic Malbolge VM (validated 1:1 against tools/trace_loop.c and against
evidence/M3_20261018/snap25445.json: full 59,049-cell memory match, 0 diffs).

MODES
  validate  re-run sim to step 25445, diff full memory vs snapshot, count prints
  search    enumerate (y, zQ, zC) with all safety constraints, rank candidates
  try       pick best (argv[2] = index, default 0), dry-run Q and C from step 0
  build     try + write work/candidate_selector_m281.mal (refuses if dry-run fails)

SCRIPT LAYOUT (consecutive cells from 25560, straight-line after sweep):

  25560 j  d := mem[155]+1 = 153
  25561 o  -> 154
  25562 /  a := stdin byte; d -> 155
  25563 o  -> 156
  25564 j  d := mem[156]+1 = 150
  25565 j  d := mem[150]+1 = 1
  25566 j  d := mem[1]+1 = 117
  25567 j  d := mem[117]+1 = 26319
  25568 j  d := mem[26319]+1 = 26099
  25569 j  d := mem[26099]+1 = 38
  25570 p  mem[38] := op(a, y) = V ; a := V ; d -> 39        (y planted at 38)
  25571 j  d := mem[39]+1 = 61
  25572 j  d := mem[61]+1 = 26319
  25573 j  d := mem[26319]+1 = 26099
  25574 j  d := mem[26099]+1 = 38
  25575 j  d := mem[38]+1 = V+1 = q          (qQ = op(81,y)+1 / qC = op(67,y)+1)
  25576 j  d := mem[q]+1 = L                 (LQ = mem[qQ]+1 / LC = mem[qC]+1)
  25577 j  d := mem[L]+1 = z+1               (z planted at L)
  25578.. o x m                              Q: -> 154 ; C: -> S
  T = 25578+m: *                             Q: mem[154] := rot(20173) = 26407
                                             C: mem[S] := rot(mem[S])
  T+1 j, T+2 o, T+3 j, T+4 i
    Q: 155->153, o->154, mem[154]=26407->26408, i->c=25976 d=26409 (loop entry)
    C: mem[S+1]=m1-1 -> m1, o -> m1+1, mem[m1+1]=H-1 -> H, i -> c=mem[H]+1 = Z

Layout relations: m = 153 - zQ ; S = zC + 154 - zQ ; script = 23+m cells.

SAFETY RULES (v2; bugs of v1 fixed: put() scoping, read-back guards):
  - plants never in script range [25560..25582+m], never at 26412/26413
    (mirrors 52826/52827 feed the mem[52828..] padding recursion)
  - qQ/qC (read by j@25576) not in script range and not plants (value must be snap)
  - s1 = S+1 not equal to LQ/LC (value must be snap; s1 itself is never planted)
  - fixed branch: h1, H must be outside script range / used / plants
  - put() failures are authoritative (nonlocal ok)
"""
import hashlib
import json
import sys
from pathlib import Path

N = 59049
NOEDIT = {26412, 26413}
XLAT1 = "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha"
XLAT2 = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
CT9 = (
    (4, 3, 3, 1, 0, 0, 1, 0, 0), (4, 3, 5, 1, 0, 2, 1, 0, 2),
    (5, 5, 4, 2, 2, 1, 2, 2, 1), (4, 3, 3, 1, 0, 0, 7, 6, 6),
    (4, 3, 5, 1, 0, 2, 7, 6, 8), (5, 5, 4, 2, 2, 1, 8, 8, 7),
    (7, 6, 6, 7, 6, 6, 4, 3, 3), (7, 6, 8, 7, 6, 8, 4, 3, 5),
    (8, 8, 7, 8, 8, 7, 5, 5, 4),
)
P9 = (1, 9, 81, 729, 6561)

ROOT = Path(__file__).resolve().parents[3]
ORIG = ROOT / "artifacts" / "candidate_m281_53562b.mal"
BASE = ROOT / "experiments" / "cat_quine_kaleidoscope"
SNAP = BASE / "evidence" / "M3_20261018" / "snap25445.json"
TABLE = BASE / "evidence" / "M3_20261018" / "cell_table_f25976.txt"
WORK = BASE / "work"
SCRIPT_START = 25560
LOOP_ENTRY = 25976


def crazy_op(x, y):
    res = 0
    for j in range(5):
        res += CT9[y // P9[j] % 9][x // P9[j] % 9] * P9[j]
    return res


def rot_op(x):
    return x // 3 + (x % 3) * 19683


def char_for_op(addr, op):
    for b in range(33, 127):
        if XLAT1[(b - 33 + addr) % 94] == op:
            return b
    raise ValueError(f"no char for {op!r} at {addr}")


def load_original():
    data = ORIG.read_bytes()
    T = [b for b in data if 33 <= b <= 126]
    assert len(T) == 52828, len(T)
    return T, pad(T)


def pad(T):
    mem = list(T)
    while len(mem) < N:
        mem.append(crazy_op(mem[-1], mem[-2]))
    return mem


def rebuild(T):
    out = bytearray()
    for i, ch in enumerate(T):
        out.append(ch)
        if (i + 1) % 72 == 0:
            out.append(10)
    out.append(10)
    return bytes(out)


def load_table():
    tbl = {}
    with open(TABLE) as f:
        next(f)
        for line in f:
            p = line.split()
            if len(p) == 7:
                c, ea, ra, wa, eb, rb, wb = (int(x) for x in p)
                tbl[c] = (ea, ra, wa, eb, rb, wb)
    return tbl


def load_snap():
    snap = json.load(open(SNAP))
    return {int(k): v for k, v in snap["mem_snapshot"].items()}


def sim(mem, stdin_bytes, max_steps=300000, stop_at_loop_c=None):
    """Exact trace_loop.c semantics. Returns dict."""
    mem = list(mem)
    c = d = a = 0
    step = prints = ip = 0
    while step < max_steps:
        if stop_at_loop_c is not None and c == stop_at_loop_c:
            return dict(reason="loop_entry", c=c, d=d, a=a, step=step,
                        prints=prints, ip=ip, mem=mem)
        v = mem[c]
        if v < 33 or v > 126:
            c = 0 if c == N - 1 else c + 1
            d = 0 if d == N - 1 else d + 1
            step += 1
            continue
        op = XLAT1[(v - 33 + c) % 94]
        if op == "j":
            d = mem[d]
        elif op == "i":
            c = mem[d]
        elif op == "*":
            a = mem[d] = rot_op(mem[d])
        elif op == "p":
            a = mem[d] = crazy_op(a, mem[d])
        elif op == "<":
            prints += 1
        elif op == "/":
            a = stdin_bytes[ip] if ip < len(stdin_bytes) else 59048
            ip += 1
        elif op == "v":
            step += 1
            return dict(reason="halt", c=c, d=d, a=a, step=step,
                        prints=prints, ip=ip, mem=mem)
        if 33 <= mem[c] <= 126:
            mem[c] = ord(XLAT2[mem[c] - 33])
        c = 0 if c == N - 1 else c + 1
        d = 0 if d == N - 1 else d + 1
        step += 1
    return dict(reason="max_steps", c=c, d=d, a=a, step=step,
                prints=prints, ip=ip, mem=mem)


def safe_sets(tbl):
    safe = set(c for c, v in tbl.items() if v == (0, 0, 0, 0, 0, 0) and c < 26414)
    pool = [c for c in range(34, 128) if c in safe and c != 38]
    return safe, pool


def build_ops(m):
    return (["j", "o", "/", "o"] + ["j"] * 6 + ["p"] + ["j"] * 7 +
            ["o"] * m + ["*", "j", "o", "j", "i"])


def find_candidates(T, momentsnap, tbl, safe, pool):
    snap = momentsnap
    valid_y = []
    for y in range(33, 127):
        vQ = crazy_op(81, y)
        vC = crazy_op(67, y)
        qQ = (vQ + 1) % N
        qC = (vC + 1) % N
        LQ = (snap[qQ] + 1) % N
        LC = (snap[qC] + 1) % N
        if LQ == LC or LQ not in safe or LC not in safe:
            continue
        if LQ in NOEDIT or LC in NOEDIT or LQ == 38 or LC == 38:
            continue
        valid_y.append((y, vQ, vC, qQ, qC, LQ, LC))
    print(f"valid y: {len(valid_y)}")

    cands = []
    for (y, vQ, vC, qQ, qC, LQ, LC) in valid_y:
        for zQ in range(33, 127):
            m = 153 - zQ
            if not (27 <= m <= 120):
                continue
            scr_lo, scr_hi = SCRIPT_START, SCRIPT_START + 22 + m
            if scr_lo <= qQ <= scr_hi or scr_lo <= qC <= scr_hi:
                continue
            for zC in range(33, 127):
                S = zC + 154 - zQ
                if not (140 <= S <= 247) or S == 154:
                    continue
                if tbl[S][4] != 0:          # loop reads S (conservative guard)
                    continue
                s1 = S + 1
                if s1 == LQ or s1 == LC:
                    continue
                m1 = (snap[s1] + 1) % N
                h1 = (m1 + 1) % N
                used = (38, LQ, LC, S, s1)
                plants = {}
                ok = True

                def put(cell, val):
                    nonlocal ok
                    if val not in range(33, 127):
                        ok = False
                        return
                    if cell in NOEDIT:
                        ok = False
                        return
                    if scr_lo <= cell <= scr_hi:
                        ok = False
                        return
                    if cell in plants:
                        if plants[cell] != val:
                            ok = False
                        return
                    plants[cell] = val

                def emit(H, Z):
                    if qQ in plants or qC in plants:
                        return False
                    cands.append((y, vQ, vC, qQ, qC, LQ, LC, m, zQ, zC, S,
                                  s1, m1, h1, H, Z, dict(plants)))
                    return True

                def chain():
                    nonlocal ok
                    if h1 in safe and h1 not in used:
                        for H in pool:
                            if H in used:
                                continue
                            base = dict(plants); ok0 = ok
                            put(h1, H - 1)
                            if ok:
                                for Z in pool:
                                    if Z in used or Z == H:
                                        continue
                                    put(H, Z - 1)
                                    if ok:
                                        put(Z, char_for_op(Z, "v"))
                                        if ok and emit(H, Z):
                                            return True
                                    plants.clear(); plants.update(base)
                                    ok = ok0
                            plants.clear(); plants.update(base); ok = ok0
                        return False
                    if h1 in used or h1 in plants or scr_lo <= h1 <= scr_hi:
                        return False
                    H = (snap[h1] + 1) % N
                    if H == S or H in used:
                        return False
                    if H in safe:
                        for Z in pool:
                            if Z in used or Z == H:
                                continue
                            base = dict(plants); ok0 = ok
                            put(H, Z - 1)
                            if ok:
                                put(Z, char_for_op(Z, "v"))
                                if ok and emit(H, Z):
                                    return True
                            plants.clear(); plants.update(base); ok = ok0
                        return False
                    if scr_lo <= H <= scr_hi:
                        return False
                    Z = (snap[H] + 1) % N
                    if Z not in safe or Z in used:
                        return False
                    put(Z, char_for_op(Z, "v"))
                    if ok and emit(H, Z):
                        return True
                    return False

                put(38, y); put(LQ, zQ); put(LC, zC)
                if ok:
                    chain()
            if len(cands) >= 4000:
                break
        if len(cands) >= 4000:
            break
    return cands


def n_edits(T, cd):
    (y, vQ, vC, qQ, qC, LQ, LC, m, zQ, zC, S, s1, m1, h1, H, Z, plants) = cd
    e = 0
    for i, op in enumerate(build_ops(m)):
        cell = SCRIPT_START + i
        if T[cell] != char_for_op(cell, op):
            e += 1
    for cell, val in plants.items():
        if T[cell] != val:
            e += 1
    return e


def apply_edits(T, cd):
    (y, vQ, vC, qQ, qC, LQ, LC, m, zQ, zC, S, s1, m1, h1, H, Z, plants) = cd
    T2 = list(T)
    edits = {}
    for i, op in enumerate(build_ops(m)):
        edits[SCRIPT_START + i] = char_for_op(SCRIPT_START + i, op)
    for cell, val in plants.items():
        if cell in edits and edits[cell] != val:
            raise SystemExit(f"conflict script/plant at {cell}")
        edits[cell] = val
    for cell, val in edits.items():
        assert 33 <= val <= 126, (cell, val)
        assert cell not in NOEDIT, (cell, val)
        assert cell + 26414 < 52826, (cell, val)
        T2[cell] = val
        T2[cell + 26414] = val
    return T2, edits


def dry_q(mem0, mem2, cd):
    (y, vQ, vC, qQ, qC, LQ, LC, m, zQ, zC, S, s1, m1, h1, H, Z, plants) = cd
    lines = []
    ent_o = sim(mem0, b"", stop_at_loop_c=LOOP_ENTRY)
    ent_p = sim(mem2, b"Q", stop_at_loop_c=LOOP_ENTRY)
    ok = True
    lines.append(f"  orig  entry: reason={ent_o['reason']} c={ent_o['c']} d={ent_o['d']} "
                 f"a={ent_o['a']} step={ent_o['step']}")
    lines.append(f"  patch entry: reason={ent_p['reason']} c={ent_p['c']} d={ent_p['d']} "
                 f"a={ent_p['a']} step={ent_p['step']} ip={ent_p['ip']}")
    if ent_o["reason"] != "loop_entry" or ent_o["step"] != 25452:
        ok = False; lines.append("  FAIL: original baseline unexpected")
    if ent_p["reason"] != "loop_entry":
        ok = False; lines.append(f"  FAIL: reason {ent_p['reason']}")
    else:
        if (ent_p["c"], ent_p["d"], ent_p["a"]) != (25976, 26409, 26407):
            ok = False; lines.append("  FAIL: entry state != (25976, 26409, 26407)")
        exp = 25468 + m
        if ent_p["step"] != exp:
            ok = False; lines.append(f"  FAIL: step {ent_p['step']} != {exp}")
        if ent_p["ip"] != 1:
            ok = False; lines.append(f"  FAIL: ip {ent_p['ip']} != 1")
    allowed = (set(range(25560, 25583 + m)) |
               set(range(25560 + 26414, 25583 + m + 26414)) |
               set(plants) | {p + 26414 for p in plants} |
               {38, 38 + 26414})
    diffs = [i for i in range(N) if mem2 is not None and
             ent_p.get("mem") is not None and ent_p["mem"][i] != ent_o["mem"][i]]
    bad = [i for i in diffs if i not in allowed]
    lines.append(f"  diffs vs original run: {len(diffs)} (allowed {len([d for d in diffs if d in allowed])}), "
                 f"outside allowed: {len(bad)}")
    if bad:
        ok = False
        lines.append(f"  FAIL: unexpected diffs at {bad[:20]}")
    return ok, lines


def dry_c(mem2, cd, p0):
    (y, vQ, vC, qQ, qC, LQ, LC, m, zQ, zC, S, s1, m1, h1, H, Z, plants) = cd
    lines = []
    r = sim(mem2, b"C", max_steps=300000, stop_at_loop_c=LOOP_ENTRY)
    lines.append(f"  C run: reason={r['reason']} c={r['c']} d={r['d']} a={r['a']} "
                 f"step={r['step']} ip={r['ip']} prints={r['prints']}")
    ok = True
    if r["reason"] != "halt":
        ok = False; lines.append(f"  FAIL: reason {r['reason']} (expected halt at Z={Z})")
    else:
        if r["c"] != Z:
            ok = False; lines.append(f"  FAIL: halt cell {r['c']} != Z {Z}")
        if r["step"] != 25469 + m:
            ok = False; lines.append(f"  FAIL: step {r['step']} != {25469 + m}")
        if r["ip"] != 1:
            ok = False; lines.append(f"  FAIL: ip {r['ip']} != 1")
        if r["prints"] != p0:
            ok = False; lines.append(f"  FAIL: prints {r['prints']} != P0 {p0}")
    return ok, lines


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "validate"
    T, mem0 = load_original()
    tbl = load_table()
    snap = load_snap()
    safe, pool = safe_sets(tbl)

    if mode == "validate":
        r = sim(mem0, b"", max_steps=25445)
        diffs = [i for i in range(N) if r["mem"][i] != snap[i]]
        print(f"step {r['step']}: c={r['c']} d={r['d']} a={r['a']} "
              f"(snap: c=25560 d=155 a=20173)")
        print(f"mem diffs vs snapshot: {len(diffs)}")
        print(f"prints during first 25445 steps (P0): {r['prints']}")
        return 0 if (len(diffs) == 0 and r["c"] == 25560 and r["d"] == 155
                     and r["a"] == 20173 and r["step"] == 25445) else 1

    cands = find_candidates(T, snap, tbl, safe, pool)
    print(f"candidates found: {len(cands)}")
    if not cands:
        return 1
    cands.sort(key=lambda cd: (n_edits(T, cd), cd[7], cd[10]))

    if mode == "search":
        for i, cd in enumerate(cands[:5]):
            (y, vQ, vC, qQ, qC, LQ, LC, m, zQ, zC, S, s1, m1, h1, H, Z, plants) = cd
            print(f"[{i}] y={y} m={m} zQ={zQ} zC={zC} S={S} LQ={LQ} LC={LC} "
                  f"h1={h1} H={H} Z={Z} edits={n_edits(T, cd)}")
            print(f"     qQ={qQ} qC={qC} m1={m1} s1={s1}")
            print(f"     plants={ {k: v for k, v in sorted(plants.items())} }")
        return 0

    idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    best = cands[idx]
    (y, vQ, vC, qQ, qC, LQ, LC, m, zQ, zC, S, s1, m1, h1, H, Z, plants) = best
    print("== candidate")
    for k, v in [("y", y), ("vQ", vQ), ("vC", vC), ("qQ", qQ), ("qC", qC),
                 ("LQ", LQ), ("LC", LC), ("m", m), ("zQ", zQ), ("zC", zC),
                 ("S", S), ("s1", s1), ("m1", m1), ("h1", h1), ("H", H), ("Z", Z)]:
        print(f"   {k} = {v}")
    print(f"   plants: { {k: v for k, v in sorted(plants.items())} }")
    print(f"   edits: {n_edits(T, best)}  script cells: {23 + m}")

    T2, edits = apply_edits(T, best)
    mem2 = pad(T2)

    p0 = sim(mem0, b"", max_steps=25445)["prints"]
    print(f"P0 = {p0}")

    ok_q, lines_q = dry_q(mem0, mem2, best)
    print("== dry-run Q")
    for ln in lines_q:
        print(ln)
    ok_c, lines_c = dry_c(mem2, best, p0)
    print("== dry-run C")
    for ln in lines_c:
        print(ln)
    if not (ok_q and ok_c):
        print("DRY-RUN FAILED - not building")
        return 1
    print("DRY-RUN OK")

    if mode == "build":
        out = rebuild(T2)
        WORK.mkdir(parents=True, exist_ok=True)
        path = WORK / "candidate_selector_m281.mal"
        path.write_bytes(out)
        print(f"wrote {path}  bytes={len(out)}  sha256={hashlib.sha256(out).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
