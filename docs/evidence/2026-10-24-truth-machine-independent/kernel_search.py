"""Busqueda M1: emisor infinito de '1' Classic Malbolge, desde cero.

Espacio: prefijos de ops DECODIFICADAS (8 ops: j i * p < / v o). Los bytes del
programa se derivan por inversion de XLAT1 por celda (solucion unica por
(op, c)); la memoria restante se llena con la ley clasica
mem[i] = crz(mem[i-1], mem[i-2]) (mb_ref.c:89). Simulacion exacta con la
semantica de tools/prove_truth_machine.py (validada contra mb_ref): tras 'i'
(c = mem[d]) la cifra post-ejecucion cae sobre la celda destino y luego c += 1.

M1 logrado: simulacion alcanza ciclo de estado completo (ventana tocada) con
>=1 output por ciclo, todos 49 ('1'), sin '/' repetido ni 'v'.
"""
from __future__ import annotations

import sys
from collections import OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from tools.prove_truth_machine import XLAT1, XLAT2, crazy  # noqa: E402

MEM_SIZE = 59049
OPS = "ji*p</vo"
XLAT1_INV = {ch: i for i, ch in enumerate(XLAT1)}
WINDOW = 4096          # celdas cacheadas/simuladas como maximo
MAX_C = MAX_D = WINDOW - 2

_tail_cache: OrderedDict[tuple[int, int], list[int]] = OrderedDict()


def op_byte(op: str, cell: int) -> int:
    return (XLAT1_INV[op] - cell) % 94 + 33


def tail_for(last2: tuple[int, int], upto: int = WINDOW) -> list[int]:
    """mem[n..upto) para un programa cuyas dos ultimas celdas son last2."""
    key = last2
    hit = _tail_cache.get(key)
    if hit is not None and len(hit) >= upto:
        _tail_cache.move_to_end(key)
        return hit
    prev2, prev1 = last2
    arr = hit if hit is not None else []
    i = len(arr)
    # reconstruir indices absolutos: la celda n-2 es prev2, n-1 es prev1
    base = 0  # arr[0] corresponde a la celda n
    while i < upto:
        v = crazy(prev1, prev2)
        arr.append(v)
        prev2, prev1 = prev1, v
        i += 1
    _tail_cache[key] = arr
    if len(_tail_cache) > 600:
        _tail_cache.popitem(last=False)
    return arr


def build_state(ops_prefix: tuple[str, ...], upto: int = WINDOW) -> list[int]:
    n = len(ops_prefix)
    assert n >= 2, "la ley de llenado clasica requiere >= 2 celdas de programa"
    prog = [op_byte(op, i) for i, op in enumerate(ops_prefix)]
    tail = tail_for((prog[-2], prog[-1]), max(0, upto - n))
    return prog + tail


def simulate(prefix: tuple[str, ...], max_steps: int = 700, warmup: int = 4):
    mem = build_state(prefix)
    a = c = d = 0
    out: list[int] = []
    seen: dict[tuple[int, int, int], tuple[int, int]] = {}
    for step in range(max_steps):
        if c >= WINDOW or d >= WINDOW:
            return {"status": "ESCAPE", "step": step, "out": out}
        v = mem[c]
        if not (33 <= v <= 126):
            return {"status": "NONPRINTABLE_PC", "step": step, "out": out}
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
            if out[-1] != 49:
                return {"status": "WRONG_OUT", "step": step, "out": out}
        elif instr == "/":
            a = 59048  # M1 sin input: EOF clasico
        elif instr == "v":
            return {"status": "HALT", "step": step, "out": out}
        if c >= WINDOW:
            return {"status": "ESCAPE", "step": step, "out": out}
        v2 = mem[c]
        if not (33 <= v2 <= 126):
            return {"status": "INVALID_ENCRYPTION", "step": step, "out": out}
        mem[c] = ord(XLAT2[v2 - 33])
        c = (c + 1) % MEM_SIZE
        d = (d + 1) % MEM_SIZE
        if c >= WINDOW or d >= WINDOW:
            return {"status": "ESCAPE", "step": step, "out": out}
        if step >= warmup:
            key = (a, c, d)
            prev = seen.get(key)
            if prev is not None:
                h = hashlib.sha256(
                    b"".join(x.to_bytes(2, "little") for x in mem[:WINDOW])
                ).hexdigest()
                if h == prev[1]:
                    period = step - prev[0]
                    return {
                        "status": "CYCLE", "step": step, "out": out,
                        "cycle_start": prev[0], "period": period,
                        "outputs_per_cycle": len(out) - prev[2],
                    }
                if key not in seen:
                    seen[key] = (step, h, len(out))  # store-first: ancla fija
            else:
                h = hashlib.sha256(
                    b"".join(x.to_bytes(2, "little") for x in mem[:WINDOW])
                ).hexdigest()
                seen[key] = (step, h, len(out))
    return {"status": "MAX_STEPS", "out": out}


def beam_search(beam_width: int = 3000, max_depth: int = 11, max_steps: int = 700):
    frontier: list[tuple[tuple[str, ...], dict]] = []
    for op1 in OPS:
        for op2 in OPS:
            prefix = (op1, op2)
            res = simulate(prefix, max_steps=max_steps)
            if res["status"] == "CYCLE":
                print(f"M1 CANDIDATE depth=2: {''.join(prefix)} -> {res}", flush=True)
            elif res["status"] == "MAX_STEPS":
                frontier.append((prefix, res))
    found = []
    best_alive = []
    for depth in range(3, max_depth + 1):
        survivors = []
        for prefix, _r in frontier:
            for op in OPS:
                cand = prefix + (op,)
                res = simulate(cand, max_steps=max_steps)
                if res["status"] == "CYCLE":
                    found.append((cand, res))
                    print(f"M1 CANDIDATE depth={depth}: {''.join(cand)} -> {res}", flush=True)
                elif res["status"] == "MAX_STEPS":
                    survivors.append((cand, res))
        survivors.sort(key=lambda t: (-len(t[1]["out"]), t[1]["step"]))
        frontier = survivors[:beam_width]
        if frontier:
            best_alive = frontier[:5]
        print(f"depth {depth}: survivors {len(survivors)} (kept {len(frontier)}), found {len(found)}", flush=True)
        if not frontier:
            break
    return found, best_alive


if __name__ == "__main__":
    import time
    t0 = time.time()
    found, alive = beam_search()
    print(f"== total M1 candidates: {len(found)} ({time.time()-t0:.1f}s)")
    for cand, res in found[:10]:
        print("".join(cand), res)
    print("== best alive (sin ciclo aun):")
    for cand, res in alive:
        print(f"  {''.join(cand)} out={len(res['out'])} status={res['status']}")


def simulate_bytes(source: bytes, payload: bytes, max_steps: int = 50000, warmup: int = 1000):
    """Motor byte-level (validacion): identico a tools/prove_truth_machine.run()."""
    mem = [b for b in source]
    n = len(mem)
    for i in range(n, MEM_SIZE):
        mem.append(crazy(mem[i - 1], mem[i - 2]))
    a = c = d = 0
    out: list[int] = []
    pending = list(payload) + [None]
    seen: dict[tuple[int, int, int], tuple[int, str, int]] = {}
    for step in range(max_steps):
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
        c = (c + 1) % MEM_SIZE
        d = (d + 1) % MEM_SIZE
        if step >= warmup:
            import hashlib
            key = (a, c, d)
            h = hashlib.sha256(b"".join(x.to_bytes(2, "little") for x in mem)).hexdigest()
            prev = seen.get(key)
            if prev is not None and prev[1] == h:
                return {"status": "CYCLE", "step": step, "out": bytes(out),
                        "cycle_start": prev[0], "period": step - prev[0]}
            if key not in seen:
                seen[key] = (step, h)  # store-first: ancla fija, igual que el prover
    return {"status": "MAX_STEPS", "step": step, "out": bytes(out)}
