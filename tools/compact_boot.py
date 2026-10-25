"""Compact BOOT builder for the Cat preamble: 1,367 -> 1,235 operations.

Canonical runtime copy of ``docs/evidence/2026-10-25-compact-cat-k18/compact_boot.py``
(origin: ``antigravity_53501039`` bridge handoff, 2026-10-25; independently verified
by ``docs/evidence/2026-10-25-compact-cat-k18/verify_k18.py`` — op-for-op identical
to the handed-over function, S3).

All four savings are inside the BOOT phase (steps 1..1434) and leave the write
phase untouched:

1. mem[89] = 58328 (the +729 odometer constant) is never installed: the k=18
   window plan (58,843..59,048, one 729-aligned block) never picks odometer
   cell 89 (measured: {92: 9, 91: 2, 90: 2, 89: 0}). Steps 515..523 collapse
   to one ``o`` and steps 1286..1341 are skipped.
2. The 51-op rotor walk on (58, 59, 60) becomes a 27-op BFS shortest path with
   the same end state (a=59048, d=61).
3. The 271-op literal setup of scratchpad 48 (steps 153..423) is rebuilt in
   239 ops, installing mem[53]=50 and mem[54]=47 first so the 3-op jump loop
   is available early.
4. mem[93] = 59048 moves from steps 630..652 to an 8-op fuse after the 1013
   solve (``ojooooop``).

Boot-end state differs from the original boot in exactly two cells — mem[59]
(rotor residue, never read again) and mem[89] (73 instead of 58328, never
read again; both facts measured in verify_k18.py S4/S5). The write phase is
byte-identical to the original-boot plan (5,964 ops, same odometer choices).
"""
from __future__ import annotations

from constants import (
    MEM_SIZE, OP_CHAR_MAP, OP_CRAZY, OP_DLOAD, OP_JMP, OP_NOP, OP_ROT,
    XLAT1, XLAT2, crazy_op, rot_op,
)
from tools.resynthesize import find_a_for_crazy, solve_sp

C59048, C59047, C59046, C29524 = 59048, 59047, 59046, 29524
CH_NOP = OP_CHAR_MAP[OP_NOP]
CH_ROT = OP_CHAR_MAP[OP_ROT]
CH_CRZ = OP_CHAR_MAP[OP_CRAZY]
CH_DLD = OP_CHAR_MAP[OP_DLOAD]
CH_JMP = OP_CHAR_MAP[OP_JMP]


def planner_fill_mem(template_clean: list[int], n: int) -> list[int]:
    """The memory model used by the synthesizer for the boot/write plan."""
    mem = list(template_clean[:1533]) + [0] * (MEM_SIZE - 1533)
    for i in range(1533, MEM_SIZE):
        mem[i] = C29524 - 81 if (i - n) % 2 == 0 else 81
    return mem


def rebuild_orig_boot_ops(template_clean: list[int], n: int) -> list[str]:
    """Reference trajectory ops for steps 0..1434 (same construction as
    ``synthesize_preamble_ops`` builds internally)."""
    m0 = planner_fill_mem(template_clean, n)
    orig: list[str] = []
    a = c = d = step = 0
    while step <= 1434:
        ch = XLAT1[(m0[c] - 33 + c) % 94]
        orig.append(ch)
        if ch == CH_DLD:
            d = m0[d]
        elif ch == CH_JMP:
            c = m0[d]
        elif ch == CH_ROT:
            m0[d] = rot_op(m0[d])
            a = m0[d]
        elif ch == CH_CRZ:
            m0[d] = crazy_op(a, m0[d])
            a = m0[d]
        m0[c] = ord(XLAT2[m0[c] - 33])
        c += 1
        d += 1
        step += 1
    return orig


def build_compact_boot(
    orig_boot_ops: list[str],
    template_clean: list[int],
    high_mods: dict[int, int],
    first_base_at_min: bool = False,
) -> tuple[list[str], list[int], int, int]:
    """Emit the compact boot plan. Returns (ops, mem, a, d) with d == 82."""
    n = len(template_clean)
    mem = planner_fill_mem(template_clean, n)
    a = 0
    d = 1
    ops_out: list[str] = []

    def sim_ops(seq: str) -> None:
        nonlocal a, d
        for ch in seq:
            ops_out.append(ch)
            if ch == CH_DLD:
                d = mem[d]
            elif ch == CH_ROT:
                mem[d] = rot_op(mem[d])
                a = mem[d]
            elif ch == CH_CRZ:
                mem[d] = crazy_op(a, mem[d])
                a = mem[d]
            d = (d + 1) % MEM_SIZE

    # 1. Steps 1..59 verbatim (48=0, 49=29524, 52=29524, 71=0, 72=29524,
    #    75=29524, 82=0, jump to d=58)
    for idx in range(1, 60):
        sim_ops(orig_boot_ops[idx])
    assert d == 58 and a == 0 and mem[58] == 41 and mem[59] == 74

    # 2. Shortest path on the (58, 59, 60) rotor: a=59048, exit at d=61
    #    (27 ops vs 51 in the original)
    sim_ops("**jp*jo*jp*jo*jp*jp*jppjpoo")
    assert d == 61 and a == 59048

    # 3. Steps 111..152 verbatim (75=59048, 52=59048, 50=59047, d=47, a=59047)
    for idx in range(111, 153):
        sim_ops(orig_boot_ops[idx])
    assert d == 47 and a == 59047 and mem[50] == 59047 and mem[51] == 0

    # 4. Install mem[53]=50 first (103 ops + "opooj" -> d=44)
    p1 = "oo*ppojoooo*ojoooopojoo*ppojo*oppojoooo*ojo*oppojoooo*ojoooo*ojoooo*ojoooo*ojoooo*ojoooo*ojoooo*ojo*opp"
    sim_ops(p1 + "opooj")
    assert d == 44 and mem[53] == 50 and a == 50

    # 5. Install mem[54]=47 using the 3-op loop j at 53 -> 51
    p2 = "*jpoj*oooojooooo*ppoj*oooojooooo*pp*jpoj*oj*oj*oj*oj*oj*oj*oj*"
    sim_ops("oooooooo" + p2 + "oopoj")
    assert d == 44 and mem[54] == 47 and a == 47
    sim_ops("ooooo")
    assert d == 49

    # 6. mem[53]=50 and mem[54]=47 are both installed: install mem[55]=93
    #    via solve_sp on scratchpad 48, replacing the final "j" of the solve
    #    with "pj" so the write lands at 55 and the jump returns to d=49.
    seq55 = solve_sp(a, mem[50], mem[51], 29431)
    sim_ops(seq55[:-1] + "pjooooo")
    assert d == 49 and mem[55] == 93

    # 7. Steps 424..458 equivalent: mem[96]=81, then mem[95]=87, d=82
    s = solve_sp(a, mem[50], mem[51], 29443)
    sim_ops(s)
    for idx in range(459, 469):
        sim_ops(orig_boot_ops[idx])
    assert d == 49 and mem[96] == 81
    s = solve_sp(a, mem[50], mem[51], 29443)
    sim_ops(s + "opj")
    assert d == 82 and mem[95] == 87

    # 8. Pre-clear sweep, skipping steps 515..523 (the unused mem[89])
    for idx in range(485, 515):
        sim_ops(orig_boot_ops[idx])
    sim_ops("o")
    for idx in range(524, 568):
        sim_ops(orig_boot_ops[idx])
    assert d == 49 and a == 29524

    # 9. Steps 568..947, skipping 630..652 (mem[93] moves to step 1020)
    boot_map_2 = {
        568: (621, 48, 29431),
        653: (662, 48, 29431),
        685: (751, 48, 29544),
        795: (848, 48, 29561),
        871: (931, 48, 29548),
    }
    b_idx = 568
    while b_idx <= 947:
        if b_idx == 630:
            b_idx = 653
        elif b_idx in boot_map_2:
            e_idx, sp_b, targ_a = boot_map_2[b_idx]
            sim_ops(solve_sp(a, mem[sp_b + 2], mem[sp_b + 3], targ_a))
            b_idx = e_idx + 1
        else:
            sim_ops(orig_boot_ops[b_idx])
            b_idx += 1
    assert d == 82 and mem[39] == 32

    for idx in range(948, 1006):
        sim_ops(orig_boot_ops[idx])
    assert d == 94

    # 10. Steps 1006..1285; "ojooooop" after the 1013 solve installs
    #     mem[93]=59048 in 8 ops
    boot_map_3 = {
        1013: (1019, 71, 59048),
        1055: (1098, 48, 29495),
        1119: (1162, 71, 59039),
        1178: (1218, 71, 59012),
        1234: (1274, 71, 58931),
    }
    b_idx = 1006
    while b_idx <= 1285:
        if b_idx in boot_map_3:
            e_idx, sp_b, targ_a = boot_map_3[b_idx]
            sim_ops(solve_sp(a, mem[sp_b + 2], mem[sp_b + 3], targ_a))
            if b_idx == 1013:
                sim_ops("ojooooop")
            b_idx = e_idx + 1
        else:
            sim_ops(orig_boot_ops[b_idx])
            b_idx += 1

    # 11. Skip 1286..1341 (56 ops installing the unused mem[89]=58328)
    assert d == 82 and mem[90] == 58814 and mem[91] == 58976 and mem[92] == 59030 and mem[93] == 59048
    b_idx = 1342
    while b_idx <= 1434:
        if b_idx == 1345:
            sim_ops(solve_sp(a, mem[35], mem[36], 29524))
            b_idx = 1352
        elif b_idx == 1367:
            min_addr = min(high_mods.keys())
            base_val = min_addr if first_base_at_min else min_addr - 1
            targ_a = find_a_for_crazy(C29524, base_val)
            sim_ops(solve_sp(a, mem[73], mem[74], targ_a))
            b_idx = 1434
        else:
            sim_ops(orig_boot_ops[b_idx])
            b_idx += 1
    sim_ops(CH_NOP + CH_DLD)
    assert d == 82
    return ops_out, mem, a, d
