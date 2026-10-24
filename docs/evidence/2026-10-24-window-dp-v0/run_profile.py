"""Perfil de costos del plan k=18 ganador (seed 9803, 7,331 ops documentadas).

Reproduce la configuracion exacta de search_seeds_10k.py (borrow_penalty=1,
direct_gap=18, restart 0.80/0.90) y desglosa las ops por fase: boot, movimientos
de base (step9 vs direct), ventanas (por ventana: base, targets, estrategia,
ops y writes con offset), y handoff final.

Salida: stdout + profile_seed9803.txt en este directorio.
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from dp_synth import extract_target_state, synthesize_preamble_ops  # noqa: E402

REF = ROOT / "reference" / "malbolge_org" / "cat.mal"
CLEAN, HIGH, HD, _ = extract_target_state(REF, 9003)
TEMPLATE = [b for b in REF.read_bytes() if 33 <= b <= 126]

K = 18
DELTA = 94 * K
BUDGET = 9003 - 94 * K - 100  # 7213

ops = synthesize_preamble_ops(
    CLEAN, HIGH, HD, 9003, delta=DELTA, template_clean=TEMPLATE,
    borrow_penalty=1, direct_gap=18,
    rng=random.Random(9803), restart_p1=0.80, restart_p2=0.90,
)
prof = synthesize_preamble_ops.profile
ph = prof["phase"]
moves = prof["moves"]
wins = prof["windows"]

lines: list[str] = []
lines.append(f"total_ops={len(ops)} budget={BUDGET} gap={len(ops) - BUDGET}")
lines.append(
    f"boot={ph['boot']} windows_block={ph['windows_done'] - ph['boot']} "
    f"handoff={ph['handoff_done'] - ph['windows_done']}"
)

step9 = [m for m in moves if m[0] == "step9"]
direct = [m for m in moves if m[0] == "direct"]
lines.append(
    f"moves: step9 n={len(step9)} ops={sum(m[3] for m in step9)} | "
    f"direct n={len(direct)} ops={sum(m[3] for m in direct)} | "
    f"total_ops={sum(m[3] for m in moves)}"
)

lines.append("")
lines.append("ventana | base | targets | n | domino/81 | ops | writes(addr,offset,len)")
win_ops_total = 0
write_ops_total = 0
offset_hist: dict[int, int] = {}
for base, addrs, strat, n_ops, writes in wins:
    win_ops_total += n_ops
    lines.append(
        f"  w | {base} | {addrs[0]}..{addrs[-1]} | {len(addrs)} | "
        f"{strat[0]}/{strat[1]} | {n_ops} | "
        + " ".join(f"({a},{o},{l})" for a, o, l in writes)
    )
    for _a, off, l in writes:
        write_ops_total += l
        offset_hist[off] = offset_hist.get(off, 0) + l

lines.append("")
lines.append(f"win_ops_total={win_ops_total} write_ops_inside_wins={write_ops_total}")
lines.append("offset->ops histograma: " + ", ".join(f"{o}:{c}" for o, c in sorted(offset_hist.items())))

# Deltas entre targets consecutivos dentro/across ventanas
all_addrs = sorted(a for _b, addrs, *_ in wins for a in addrs)
gaps = [b - a for a, b in zip(all_addrs, all_addrs[1:])]
from collections import Counter  # noqa: E402
lines.append("gap histograma (distancia entre targets consecutivos): "
              + ", ".join(f"{g}:{c}" for g, c in sorted(Counter(gaps).items())))

out = "\n".join(lines)
print(out)
(HERE / "profile_seed9803.txt").write_text(out + "\n")
