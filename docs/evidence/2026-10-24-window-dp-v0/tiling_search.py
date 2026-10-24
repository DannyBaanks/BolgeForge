"""Busqueda de tilings de ventanas (local search sobre bordes + merges + cap).

Base: plan k=18 seed 9803 (7,331 ops documentadas; budget 7,213).
Vecinos: desplazar cada borde entre ventanas consecutivas +-1/+-2 targets,
fusionar ventanas adyacentes, y cap de offset 9/10/11 con tiling greedy.
Costo evaluado con el simulador real de dp_synth2 (no modelo aproximado).
"""
import random
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from dp_synth2 import extract_target_state, synthesize_preamble_ops  # noqa: E402

REF = ROOT / "reference" / "malbolge_org" / "cat.mal"
CLEAN, HIGH, HD, _ = extract_target_state(REF, 9003)
TEMPLATE = [b for b in REF.read_bytes() if 33 <= b <= 126]
K = 18
DELTA = 94 * K
SEED = 9803
KW = dict(
    delta=DELTA, template_clean=TEMPLATE, borrow_penalty=1, direct_gap=18,
    rng=random.Random(SEED), restart_p1=0.80, restart_p2=0.90,
)

N = len(HIGH)
SORTED_ADDRS = sorted(HIGH.keys())


def eval_job(job):
    tiling, cap = job
    ops = synthesize_preamble_ops(CLEAN, HIGH, HD, 9003, tiling=tiling, window_cap=cap, **KW)
    return (len(ops), tiling, cap)


def greedy_tiling(cap):
    """Corre greedy con el cap dado y extrae la particion de sorted_addrs."""
    ops = synthesize_preamble_ops(CLEAN, HIGH, HD, 9003, window_cap=cap, **KW)
    wins = synthesize_preamble_ops.profile["windows"]
    slices = []
    j = 0
    for _base, addrs, _s, _n, _w in wins:
        last = addrs[-1]
        k = j
        while SORTED_ADDRS[k] != last:
            k += 1
        slices.append(SORTED_ADDRS[j:k + 1])
        j = k + 1
    assert j == len(SORTED_ADDRS), (j, len(SORTED_ADDRS))
    return ops, slices


if __name__ == "__main__":
    # 1) Punto de partida: greedy caps 9/10/11
    starts = []
    with Pool(3) as pool:
        for (n_ops, tiling, cap) in pool.map(eval_job, [(None, c) for c in (9, 10, 11)]):
            starts.append((n_ops, tiling, cap))
    for n_ops, _t, cap in starts:
        print(f"greedy cap={cap}: {n_ops}")
    n_greedy9, tiling9, _ = starts[0]
    # tiling del greedy cap9 reconstruido desde win_log
    _ops9, tiling0 = greedy_tiling(9)

    # 2) Vecinos: shifts de borde y merges
    def neighbors(til):
        out = []
        for b in range(1, len(til)):
            for shift in (1, 2):
                if b - 1 >= 0 and len(til[b - 1]) > shift:
                    t2 = [list(g) for g in til]
                    moved = t2[b - 1][-shift:]
                    t2[b - 1] = t2[b - 1][:-shift]
                    t2[b] = moved + t2[b]
                    out.append((t2, 9, f"shift{shift}@b{b}R"))
                if len(til[b]) > shift:
                    t2 = [list(g) for g in til]
                    moved = t2[b][:shift]
                    t2[b] = t2[b][shift:]
                    t2[b - 1] = t2[b - 1] + moved
                    out.append((t2, 9, f"shift{shift}@b{b}L"))
            if len(til[b - 1]) + len(til[b]) <= 12:
                t2 = [list(g) for g in til]
                t2[b - 1] = t2[b - 1] + t2[b]
                del t2[b]
                out.append((t2, 9, f"merge@b{b}"))
        return out

    best_n, best_t, best_cap = min(starts, key=lambda r: r[0])
    if best_t is None:
        best_t = tiling0
        best_cap = 9
    print(f"start best: {best_n} (cap {best_cap}, {len(best_t)} ventanas)")

    for rnd in range(3):
        neigh = neighbors(best_t)
        jobs = [(t, 9) for t, _c, _tag in neigh]
        with Pool(12) as pool:
            results = pool.map(eval_job, jobs)
        scored = sorted(zip(results, [tag for _t, _c, tag in neigh], strict=True), key=lambda r: r[0][0])
        top = scored[0]
        print(f"round {rnd}: best neighbor {top[0][0]} ({top[1]}) vs current {best_n}")
        if top[0][0] < best_n:
            best_n, best_t, best_cap = top[0][0], top[0][1], top[0][2]
        else:
            print("sin mejora; paro")
            break

    print(f"BEST: {best_n} ops (tiling cap={best_cap}, {len(best_t)} ventanas) gap_vs_budget={best_n - (9003 - 94*K - 100)}")
    (HERE / "best_tiling.txt").write_text(repr(best_t) + "\n")
    # 3) Re-busqueda de semillas sobre el mejor tiling
    def seed_job(seed):
        opsl = synthesize_preamble_ops(
            CLEAN, HIGH, HD, 9003, tiling=best_t, window_cap=best_cap,
            delta=DELTA, template_clean=TEMPLATE, borrow_penalty=1, direct_gap=18,
            rng=random.Random(seed), restart_p1=0.80, restart_p2=0.90)
        return seed, len(opsl)
    with Pool(12) as pool:
        rows = pool.map(seed_job, range(2000), chunksize=8)
    rows.sort(key=lambda r: r[1])
    print(f"seeds2000 sobre best tiling: min {rows[0][1]} seed {rows[0][0]} best10 {rows[:10]}")
