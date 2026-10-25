"""Solver mecanico v4: Truth Machine independiente (Classic Malbolge).

Idea central: la rama la produce el segundo 'p', que deja a = W2(a) en el
registro.  Si W2(49) = 49 entonces:
  - el salto 'i' cae en la celda 49 -> cifra -> ejecuta 50 (gobierno),
  - y el registro ya vale 49, asi que el '<' del kernel emite '1' para siempre.
La rama va INMEDIATAMENTE tras el segundo 'p' para que j0 = k+1 <= 49 < 50:
la celda 50 queda fuera del camino de entrada.

Entrada: '/'@0, '<'@1, 'j'@2 (d:=38, byte propio), NOPs, 'p'@pc1 -> D1=pc1+36,
         NOPs, 'p'@pc2 -> D2=pc2+36 (W2), 'j'@k -> d:=mem[k+36]=D2-1,
         'i'@(k+1) -> c:=mem[D2]=W2(a).

Rama (+1 post-salto):
  '1': c:=49 -> enc@49 -> ejecuta 50 = 'i' con d=rv -> c:=mem[rv]=87 (R2)
       -> enc@87 -> O@88 (d=rv+1) -> G@89 (d=rv+2).  rv = D2+1.
  '0': c:=W2_48 -> enc -> ejecuta W2_48+1 = 'v' -> HALT.

Ventana (trace real, rv=47): mem[rv]=87, mem[rv+2]=63, mem[rv+4]=63,
mem[rv+5]=rv-1; libres rv+1 (d de O) y rv+3.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from tools.prove_truth_machine import XLAT1, XLAT2, crazy
from kernel_search import simulate_bytes

XI = {ch: i for i, ch in enumerate(XLAT1)}
def op_byte(op, P): return (XI[op] - P) % 94 + 33

T, R1, I = 64, 63, 65
O, R2, G = 88, 87, 89
KERNEL = {R1, T, I, R2, O, G}
BRANCH = 49          # W2(49) = 49 -> a = 49 y celda 50 = gobierno

def branch_pairs():
    hits = []
    for y1 in range(33, 127):
        if y1 % 9 not in (0, 1):
            continue
        W1_48, W1_49 = crazy(48, y1), crazy(49, y1)
        for y2 in range(33, 127):
            if crazy(W1_49, y2) != BRANCH:
                continue
            W2_48 = crazy(W1_48, y2)
            if W2_48 == BRANCH:
                continue
            if not (33 <= W2_48 <= 240):
                continue
            hits.append((y1, y2, W2_48))
    return hits

def build(y1, y2, D2, pc1, k, W2_48):
    rv = D2 + 1
    pc2 = D2 - 36
    j0 = k + 1
    H48 = W2_48
    n = max(j0, rv + 6, G, D2, k + 36, H48 + 2, BRANCH + 1) + 1
    src = [33] * n
    used = {}
    def put(pos, val, tag):
        if pos < 0 or pos >= n:
            return f"{tag} fuera de rango ({pos})"
        if pos in used:
            return f"colision en {pos}: {used[pos]} vs {tag}"
        used[pos] = tag
        src[pos] = val
        return None
    def put_op(pos, op, tag):
        return put(pos, op_byte(op, pos), f"{tag}({op})")
    msgs = []
    msgs.append(put(0, op_byte('/', 0), "slash"))
    msgs.append(put(1, op_byte('<', 1), "emit"))
    msgs.append(put(2, op_byte('j', 2), "j2"))
    msgs.append(put_op(pc1, 'p', "p1"))
    msgs.append(put_op(pc2, 'p', "p2"))
    msgs.append(put_op(k, 'j', "jk"))
    msgs.append(put_op(j0, 'i', "ibranch"))
    msgs.append(put(D1 := pc1 + 36, y1, "D1"))
    msgs.append(put(k + 36, D2 - 1, "jtarget"))
    msgs.append(put(R1, 33, "R1"))
    msgs.append(put(T, 74, "T"))
    msgs.append(put(I, op_byte('i', I), "I"))
    msgs.append(put(R2, 33, "R2"))
    msgs.append(put(O, 114, "O"))
    msgs.append(put(G, op_byte('i', G), "G"))
    msgs.append(put(D2, y2, "D2(R2slot)"))
    msgs.append(put(rv, R2, "rv"))
    msgs.append(put(rv + 2, R1, "rv2"))
    msgs.append(put(rv + 4, R1, "rv4"))
    msgs.append(put(rv + 5, rv - 1, "rv5"))
    msgs.append(put(BRANCH + 1, op_byte('i', BRANCH + 1), "steer1"))
    if H48 + 1 == BRANCH:
        msgs.append(put(H48 + 1, op_byte('v', H48 + 1), "v0=steer1"))
    else:
        msgs.append(put(H48, 33, "h48"))
        msgs.append(put(H48 + 1, op_byte('v', H48 + 1), "v0"))
    for m in msgs:
        if m:
            return None, m
    for c in range(3, j0):
        if c not in used:
            src[c] = op_byte('o', c)
    for c, b in enumerate(src):
        if not (33 <= b <= 126):
            return None, f"byte no imprimible en {c} ({b})"
    return src, None

WIN = 256

def _fast(src, payload, max_steps, warmup):
    import hashlib
    mem = [b for b in src]
    while len(mem) < WIN:
        mem.append(crazy(mem[-1], mem[-2]))
    a = c = d = 0
    out = []
    pending = list(payload) + [None]
    seen = {}
    for step in range(max_steps):
        if c >= WIN or d >= WIN:
            return {"status": "ESCAPE", "step": step, "out": bytes(out)}
        v = mem[c]
        if not (33 <= v <= 126):
            return {"status": "NONPRINTABLE_PC", "step": step, "out": bytes(out)}
        instr = XLAT1[(v - 33 + c) % 94]
        if instr == "j":
            d = mem[d]
        elif instr == "i":
            c = mem[d]
        elif instr == "*":
            a = mem[d] = mem[d] // 3 + mem[d] % 3 * 19683
        elif instr == "p":
            a = mem[d] = crazy(a, mem[d])
        elif instr == "<":
            out.append(a & 255)
        elif instr == "/":
            val = pending.pop(0) if pending else None
            a = 59048 if val is None else val
        elif instr == "v":
            return {"status": "HALT", "step": step, "out": bytes(out)}
        v2 = mem[c]
        if not (33 <= v2 <= 126):
            return {"status": "INVALID_ENCRYPTION", "step": step, "out": bytes(out)}
        mem[c] = ord(XLAT2[v2 - 33])
        c = (c + 1) % 59049
        d = (d + 1) % 59049
        if step >= warmup:
            key = (a, c, d)
            h = hashlib.sha256(bytes(x & 255 for x in mem[:WIN])).digest()
            prev = seen.get(key)
            if prev is not None and prev[1] == h:
                return {"status": "CYCLE", "step": step, "out": bytes(out),
                        "cycle_start": prev[0], "period": step - prev[0]}
            if key not in seen:
                seen[key] = (step, h)
    return {"status": "MAX_STEPS", "step": step, "out": bytes(out)}

def check(src):
    r0 = _fast(src, b"0", 4000, 600)
    if not (r0["status"] == "HALT" and r0["out"] == b"0"):
        return False, r0, None
    r1 = _fast(src, b"1", 8000, 600)
    ok1 = (r1["status"] == "CYCLE" and r1["out"][:1] == b"1"
           and set(r1["out"][1:]) == {0x31})
    return ok1, r0, r1

if __name__ == "__main__":
    from collections import Counter
    pairs = branch_pairs()
    print(f"pares con W2(49)=49: {len(pairs)}")
    built = tried = 0
    reasons = Counter()
    for y1, y2, W2_48 in pairs:
        for D2 in range(74, 81):
            pc2 = D2 - 36
            for k in range(max(pc2 + 1, 45), 49):
                if k + 36 in range(D2, D2 + 7):
                    continue
                for pc1 in range(3, pc2):
                    src, err = build(y1, y2, D2, pc1, k, W2_48)
                    if src is None:
                        reasons[err] += 1
                        continue
                    built += 1
                    ok, r0, r1 = check(src)
                    tried += 1
                    if ok:
                        print(f"*** TM INDEPENDIENTE *** y1={y1} y2={y2} D2={D2} "
                              f"pc1={pc1} k={k} W2_48={W2_48} n={len(src)}")
                        print("   in0:", r0["status"], r0.get("step"), r0["out"])
                        print("   in1:", r1["status"], "period", r1.get("period"),
                              "out_len", len(r1["out"]))
                        (HERE / "candidate_source.txt").write_text(
                            "".join(chr(b) for b in src) + "\n")
                        (HERE / "candidate_bytes.txt").write_text(
                            " ".join(str(b) for b in src) + "\n")
                        (HERE / "candidate_params.json").write_text(
                            f'{{"y1": {y1}, "y2": {y2}, "D2": {D2}, "pc1": {pc1}, '
                            f'"k": {k}, "W2_48": {W2_48}, "n": {len(src)}}}\n')
                        sys.exit(0)
                    reasons[f"sim:{r0['status']}/{(r1['status'] if r1 else '-')}"] += 1
    print(f"sin candidato: construidas {built}, simuladas {tried}")
    print(reasons.most_common(12))
