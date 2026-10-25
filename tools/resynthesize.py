#!/usr/bin/env python3
"""tools/resynthesize.py - Real, mb_ref-verified preamble compressor for malbolge.org programs."""
from __future__ import annotations

import argparse
import ctypes
import tempfile
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from constants import (
    rot_op,
    crazy_op,
    XLAT1,
    XLAT2,
    MEM_SIZE,
    OP_JMP,
    OP_ROT,
    OP_DLOAD,
    OP_CRAZY,
    OP_NOP,
    OP_CHAR_MAP,
)

C59048, C59047, C59046, C29524 = 59048, 59047, 59046, 29524
CH_NOP = OP_CHAR_MAP[OP_NOP]
CH_ROT = OP_CHAR_MAP[OP_ROT]
CH_CRZ = OP_CHAR_MAP[OP_CRAZY]
CH_DLD = OP_CHAR_MAP[OP_DLOAD]
CH_JMP = OP_CHAR_MAP[OP_JMP]

INV_CRZ = {
    (0, 1): 0, (0, 0): 1,
    (1, 1): 0, (1, 0): 1, (1, 2): 2,
    (2, 2): 0, (2, 1): 2,
}

C_SOLVER_SRC = r"""
#include <stdint.h>
#include <string.h>

#define MEM_SIZE 59049
#define C59048 59048
#define C59047 59047
#define C59046 59046
#define C29524 29524

static uint16_t rot_arr[MEM_SIZE];
static uint16_t crz48_arr[MEM_SIZE];
static uint16_t crzxx_arr[MEM_SIZE];
static uint16_t crz00_arr[MEM_SIZE];
static uint16_t crz47_arr[MEM_SIZE];
static uint16_t crz24_arr[MEM_SIZE];
static uint16_t crz46_arr[MEM_SIZE];
static int initialized = 0;

static uint16_t crz(uint16_t x, uint16_t y) {
    static const uint16_t tbl[3][3] = {{1, 0, 0}, {1, 0, 2}, {2, 2, 1}};
    uint16_t res = 0, p = 1;
    for (int i = 0; i < 10; i++) {
        res += tbl[y % 3][x % 3] * p;
        x /= 3; y /= 3; p *= 3;
    }
    return res;
}

void init_tables(void) {
    if (initialized) return;
    for (int x = 0; x < MEM_SIZE; x++) {
        rot_arr[x] = (x / 3) + (x % 3) * 19683;
        crz48_arr[x] = crz(C59048, x);
        crzxx_arr[x] = crz(x, x);
        crz00_arr[x] = crz(0, x);
        crz47_arr[x] = crz(C59047, x);
        crz24_arr[x] = crz(C29524, x);
        crz46_arr[x] = crz(C59046, x);
    }
    initialized = 1;
}

int solve_sp_c(int a_in, int temp_in, int x_in, int a_target, char *out_buf) {
    init_tables();
    static uint8_t dist[MEM_SIZE];
    static int32_t parent[MEM_SIZE];
    static uint8_t move_id[MEM_SIZE];
    static char init_prefix[MEM_SIZE][12];
    static uint16_t buckets[120][MEM_SIZE];
    static int b_len[120];

    memset(dist, 255, sizeof(dist));
    memset(b_len, 0, sizeof(b_len));

    const char ops1[2] = {'o', '*'};
    const char ops2[2] = {'o', 'p'};
    const char ops3[3] = {'o', '*', 'p'};

    for (int i1 = 0; i1 < 2; i1++) {
        char op1 = ops1[i1];
        int a1 = (op1 == '*') ? C29524 : a_in;
        for (int i2 = 0; i2 < 2; i2++) {
            char op2 = ops2[i2];
            if (op2 == 'p' && a1 != 0 && a1 != C29524) continue;
            int t2 = (op2 == 'p') ? crz(a1, temp_in) : temp_in;
            int a2 = (op2 == 'p') ? t2 : a1;
            for (int i3 = 0; i3 < 3; i3++) {
                char op3 = ops3[i3];
                int x3, a3;
                if (op3 == 'o') { x3 = x_in; a3 = a2; }
                else if (op3 == '*') { x3 = a3 = rot_arr[x_in]; }
                else { x3 = a3 = crz(a2, x_in); }

                if (a3 == a_target) {
                    out_buf[0] = op1; out_buf[1] = op2; out_buf[2] = op3;
                    strcpy(out_buf + 3, "oooj");
                    return 7;
                }
                if (C59048 == a_target) {
                    out_buf[0] = op1; out_buf[1] = op2; out_buf[2] = op3;
                    strcpy(out_buf + 3, "*ooj");
                    return 7;
                }
                if (a3 == x3) {
                    if (3 < dist[x3]) {
                        dist[x3] = 3;
                        parent[x3] = -1;
                        init_prefix[x3][0] = op1;
                        init_prefix[x3][1] = op2;
                        init_prefix[x3][2] = op3;
                        init_prefix[x3][3] = 0;
                        buckets[3][b_len[3]++] = x3;
                    }
                } else {
                    int n6[3] = {rot_arr[x3], crz48_arr[x3], crz(a3, x3)};
                    const char *s6[3] = {"oj*", "*jp", "ojp"};
                    for (int m = 0; m < 3; m++) {
                        int xn = n6[m];
                        if (6 < dist[xn]) {
                            dist[xn] = 6;
                            parent[xn] = -1;
                            init_prefix[xn][0] = op1;
                            init_prefix[xn][1] = op2;
                            init_prefix[xn][2] = op3;
                            strcpy(init_prefix[xn] + 3, s6[m]);
                            buckets[6][b_len[6]++] = xn;
                        }
                    }
                    int n10[4] = {crz00_arr[x3], crz47_arr[x3], crz24_arr[x3], crz46_arr[x3]};
                    const char *s10[4] = {"ooj*oop", "ooj*opp", "oojo*op", "oojo*pp"};
                    for (int m = 0; m < 4; m++) {
                        int xn = n10[m];
                        if (10 < dist[xn]) {
                            dist[xn] = 10;
                            parent[xn] = -1;
                            init_prefix[xn][0] = op1;
                            init_prefix[xn][1] = op2;
                            init_prefix[xn][2] = op3;
                            strcpy(init_prefix[xn] + 3, s10[m]);
                            buckets[10][b_len[10]++] = xn;
                        }
                    }
                }
            }
        }
    }

    static const char *m_str[7] = {
        "oj*", "*jp", "ojp",
        "ooj*oop", "ooj*opp", "oojo*op", "oojo*pp"
    };

    for (int cost = 3; cost < 110; cost++) {
        int len = b_len[cost];
        for (int i = 0; i < len; i++) {
            int x = buckets[cost][i];
            if (cost > dist[x]) continue;
            if (x == a_target) {
                int stack[32], slen = 0;
                int cur = x;
                while (parent[cur] != -1) {
                    stack[slen++] = move_id[cur];
                    cur = parent[cur];
                }
                strcpy(out_buf, init_prefix[cur]);
                for (int k = slen - 1; k >= 0; k--) {
                    strcat(out_buf, m_str[stack[k]]);
                }
                strcat(out_buf, "oooj");
                return (int)strlen(out_buf);
            }

            int c3 = cost + 3;
            int n3[3] = {rot_arr[x], crz48_arr[x], crzxx_arr[x]};
            for (int m = 0; m < 3; m++) {
                int nx = n3[m];
                if (c3 < dist[nx]) {
                    dist[nx] = c3;
                    parent[nx] = x;
                    move_id[nx] = m;
                    buckets[c3][b_len[c3]++] = nx;
                }
            }

            int c7 = cost + 7;
            int n7[4] = {crz00_arr[x], crz47_arr[x], crz24_arr[x], crz46_arr[x]};
            for (int m = 0; m < 4; m++) {
                int nx = n7[m];
                if (c7 < dist[nx]) {
                    dist[nx] = c7;
                    parent[nx] = x;
                    move_id[nx] = 3 + m;
                    buckets[c7][b_len[c7]++] = nx;
                }
            }
        }
    }
    return -1;
}
"""


def _load_c_solver() -> ctypes.CDLL:
    build_dir = REPO_ROOT / ".build"
    build_dir.mkdir(exist_ok=True)
    c_path = build_dir / "sp_solver.c"
    so_path = build_dir / "sp_solver.so"
    if not so_path.exists() or not c_path.exists() or c_path.read_text() != C_SOLVER_SRC:
        c_path.write_text(C_SOLVER_SRC)
        subprocess.run(
            ["gcc", "-O3", "-shared", "-fPIC", str(c_path), "-o", str(so_path)],
            check=True,
        )
    lib = ctypes.CDLL(str(so_path))
    lib.solve_sp_c.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
    lib.solve_sp_c.restype = ctypes.c_int
    return lib


_LIB = _load_c_solver()
_BUF = ctypes.create_string_buffer(256)
_SP_CACHE: dict[tuple[int, int, int, int], str] = {}


def solve_sp(a_in: int, temp_in: int, x_in: int, a_target: int) -> str:
    key = (a_in, temp_in, x_in, a_target)
    res = _SP_CACHE.get(key)
    if res is not None:
        return res
    n = _LIB.solve_sp_c(a_in, temp_in, x_in, a_target, _BUF)
    if n < 0:
        raise RuntimeError(f"Unreachable target {a_target}")
    res = _BUF.value.decode("ascii")
    if len(_SP_CACHE) < 200000:
        _SP_CACHE[key] = res
    return res


def find_a_for_crazy(old_val: int, new_val: int) -> int | None:
    a, p, y, z = 0, 1, old_val, new_val
    for _ in range(10):
        yt, zt = y % 3, z % 3
        if (yt, zt) not in INV_CRZ:
            return None
        a += INV_CRZ[(yt, zt)] * p
        y //= 3
        z //= 3
        p *= 3
    return a


def extract_target_state(prog_path: Path, lin_end: int) -> tuple[list[int], dict[int, int], int, int]:
    raw = prog_path.read_bytes()
    clean = [b for b in raw if 33 <= b <= 126]
    n = len(clean)
    mem = list(clean) + [0] * (MEM_SIZE - n)
    for i in range(n, MEM_SIZE):
        mem[i] = crazy_op(mem[i - 1], mem[i - 2])
    init_mem = list(mem)

    a = c = d = 0
    for _ in range(1000000):
        if not 33 <= mem[c] <= 126:
            raise ValueError(f"Nonprintable preamble instruction at {c}")
        ch = XLAT1[(mem[c] - 33 + c) % 94]
        if c == lin_end:
            if ch != CH_JMP:
                raise ValueError("Preamble handoff must be a jump")
            handoff_d = d
            handoff_c_target = mem[d]
            break
        if ch in '</v':
            raise ValueError("Preamble boundary reached I/O or HALT before handoff")
        if ch == CH_DLD:
            d = mem[d]
        elif ch == CH_JMP:
            c = mem[d]
        elif ch == CH_ROT:
            mem[d] = rot_op(mem[d])
            a = mem[d]
        elif ch == CH_CRZ:
            mem[d] = crazy_op(a, mem[d])
            a = mem[d]
        if not 33 <= mem[c] <= 126:
            raise ValueError(f"Invalid preamble encryption at {c}")
        mem[c] = ord(XLAT2[mem[c] - 33])
        c = (c + 1) % MEM_SIZE
        d = (d + 1) % MEM_SIZE
    else:
        raise ValueError("Preamble handoff not reached within 1000000 steps")

    high_mods = {i: mem[i] for i in range(n, MEM_SIZE) if mem[i] != init_mem[i]}
    return clean, high_mods, handoff_d, handoff_c_target


BOOT_INTERVALS = (
    (424, 458, 48, 29443), (469, 481, 48, 29443), (568, 621, 48, 29431),
    (630, 636, 48, 59048), (653, 662, 48, 29431), (685, 751, 48, 29544),
    (795, 848, 48, 29561), (871, 931, 48, 29548), (965, 971, 71, 29524),
    (1013, 1019, 71, 59048), (1055, 1098, 48, 29495), (1119, 1162, 71, 59039),
    (1178, 1218, 71, 59012), (1234, 1274, 71, 58931), (1290, 1330, 71, 58688),
    (1345, 1351, 33, 29524), (1367, 1433, 71, 58890),
)
BOOT_START_MAP = {s: (e, b, targ) for s, e, b, targ in BOOT_INTERVALS}


def synthesize_preamble_ops(
    clean: list[int],
    high_mods: dict[int, int],
    handoff_d: int,
    lin_end: int,
    delta: int,
    template_clean: list[int] | None = None,
    *,
    borrow_penalty: int = 8,
    direct_gap: int = 27,
    rng=None,
    restart_p1: float = 0.60,
    restart_p2: float = 0.75,
    boot: str = "original",
) -> list[str]:
    if template_clean is None:
        template_clean = clean
    n = len(clean)
    m0 = list(template_clean[:1533]) + [0] * (MEM_SIZE - 1533)
    for i in range(1533, MEM_SIZE):
        m0[i] = C29524 - 81 if (i - n) % 2 == 0 else 81

    orig_boot_ops: list[str] = []
    a0 = c0 = d0 = step0 = 0
    while step0 <= 1434:
        ch = XLAT1[(m0[c0] - 33 + c0) % 94]
        orig_boot_ops.append(ch)
        if ch == CH_DLD:
            d0 = m0[d0]
        elif ch == CH_JMP:
            c0 = m0[d0]
        elif ch == CH_ROT:
            m0[d0] = rot_op(m0[d0])
            a0 = m0[d0]
        elif ch == CH_CRZ:
            m0[d0] = crazy_op(a0, m0[d0])
            a0 = m0[d0]
        m0[c0] = ord(XLAT2[m0[c0] - 33])
        c0 += 1
        d0 += 1
        step0 += 1

    mem = list(template_clean[:1533]) + [0] * (MEM_SIZE - 1533)
    for i in range(1533, MEM_SIZE):
        mem[i] = C29524 - 81 if (i - n) % 2 == 0 else 81

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

    if boot == "compact":
        # Compact boot (1,235 ops): the four BOOT savings documented in
        # tools/compact_boot.py and evidenced in
        # docs/evidence/2026-10-25-compact-cat-k18/. Leaves the write phase
        # byte-identical (verified S5: same 5,964 ops, same odometer picks).
        from tools.compact_boot import build_compact_boot

        ops_b, mem_b, a_b, d_b = build_compact_boot(orig_boot_ops, template_clean, high_mods)
        ops_out.extend(ops_b)
        mem[:] = mem_b
        a, d = a_b, d_b
        assert d == 82
    elif boot == "original":
        b_idx = 1
        while b_idx <= 1434:
            if b_idx in BOOT_START_MAP:
                end_idx, sp_b, targ_a = BOOT_START_MAP[b_idx]
                if b_idx == 1367:
                    min_addr = min(high_mods.keys())
                    targ_a = find_a_for_crazy(C29524, min_addr - 1)
                    assert targ_a is not None
                seq = solve_sp(a, mem[sp_b + 2], mem[sp_b + 3], targ_a)
                sim_ops(seq)
                b_idx = end_idx + 1
            else:
                sim_ops(orig_boot_ops[b_idx])
                b_idx += 1

        sim_ops(CH_NOP + CH_DLD)
        assert d == 82
    else:
        raise ValueError(f"unknown boot mode: {boot!r}")

    RESET_94_SEQ = (
        CH_NOP * 2 + CH_DLD + CH_ROT + CH_NOP * 5 + CH_DLD
        + CH_CRZ + CH_DLD + CH_NOP * 6 + CH_CRZ + CH_NOP + CH_DLD
    )

    def set_dest_94_direct(new_dest: int) -> None:
        curr_94 = mem[94]
        if curr_94 == new_dest:
            return
        if new_dest == curr_94 + 9:
            old_94 = mem[94]
            for k_cell in (92, 91, 90, 89):
                m88 = crazy_op(C29524, mem[88])
                v1 = crazy_op(C59048, old_94)
                m88_2 = crazy_op(v1, m88)
                mk = crazy_op(m88_2, mem[k_cell])
                if crazy_op(mk, v1) == new_dest:
                    mid = [CH_NOP] * 4
                    mid[k_cell - 89] = CH_CRZ
                    seq = (
                        CH_NOP * 5 + CH_ROT + CH_CRZ + CH_NOP * 4 + CH_ROT + CH_CRZ + CH_DLD
                        + CH_CRZ + "".join(mid) + CH_NOP + CH_CRZ + CH_NOP + CH_DLD
                    )
                    sim_ops(seq)
                    assert d == 82 and mem[94] == new_dest
                    return

        a_req = find_a_for_crazy(curr_94, new_dest)
        if a_req is None:
            sim_ops(RESET_94_SEQ)
            assert d == 82 and mem[94] == C29524
            curr_94 = C29524
            a_req = find_a_for_crazy(curr_94, new_dest)
            assert a_req is not None

        sp_ops = solve_sp(a, mem[71 + 2], mem[71 + 3], a_req)
        sim_ops(CH_NOP * 3 + CH_DLD + sp_ops + CH_CRZ + CH_NOP + CH_DLD)
        assert d == 82 and mem[94] == new_dest

    def return_to_82_from(addr: int, mem_arr: list[int]) -> str:
        if addr >= 59047:
            steps_to_1 = 59049 - addr
            return CH_NOP * steps_to_1 + CH_DLD + CH_NOP
        r = addr + 1
        while r < 59049 and mem_arr[r] != 81:
            r += 1
        if r < 59049:
            return CH_NOP * (r - addr - 1) + CH_DLD
        steps_to_1 = 59049 - addr
        return CH_NOP * steps_to_1 + CH_DLD + CH_NOP

    def best_write_seq_for_addr(addr: int, base_dest: int, target_val: int) -> str:
        curr_val = mem[addr]
        offset = addr - base_dest
        ret_ops = return_to_82_from(addr, mem)
        prefix_preclear = ""
        a_after_pre = a
        if find_a_for_crazy(curr_val, target_val) is None:
            prefix_preclear = (
                CH_ROT + CH_DLD + CH_DLD
                + CH_NOP * (offset - 1)
                + CH_CRZ + ret_ops
            )
            curr_val = C29524
            a_after_pre = C29524

        a_req = find_a_for_crazy(curr_val, target_val)
        assert a_req is not None

        if a_after_pre == a_req:
            compute_and_jump = CH_NOP + CH_DLD + CH_DLD
        elif a_req == 0:
            compute_and_jump = CH_ROT + CH_DLD + CH_DLD
        else:
            orig_val = high_mods[addr]
            if lin_end < orig_val < n:
                home_sp = 33
            elif orig_val < 2000 or orig_val == 29443:
                home_sp = 48
            else:
                home_sp = 71

            all_sps = (
                (33, CH_NOP * 2 + CH_DLD, CH_ROT + CH_NOP + CH_DLD),
                (71, CH_NOP * 3 + CH_DLD, CH_ROT + CH_NOP * 2 + CH_DLD),
                (48, CH_NOP * 4 + CH_DLD, CH_ROT + CH_NOP * 3 + CH_DLD),
            )
            best_sp = None
            best_sp_score = 10**9
            for sp_base, nop_entry, z_entry in all_sps:
                s1 = nop_entry + solve_sp(a_after_pre, mem[sp_base + 2], mem[sp_base + 3], a_req)
                s2 = z_entry + solve_sp(0, mem[sp_base + 2], mem[sp_base + 3], a_req)
                cand = s1 if len(s1) <= len(s2) else s2
                borrow_pen = 0 if (sp_base == home_sp or mem[sp_base + 3] == a_req) else borrow_penalty
                if len(cand) + borrow_pen < best_sp_score:
                    best_sp_score = len(cand) + borrow_pen
                    best_sp = cand
            assert best_sp is not None
            compute_and_jump = best_sp + CH_DLD

        return prefix_preclear + compute_and_jump + CH_NOP * (offset - 1) + CH_CRZ + ret_ops

    def run_window_strategy(window: list[tuple[int, int]], use_domino: bool, respect_81: bool) -> str:
        nonlocal a, d
        saved_mem_low = mem[30:99]
        saved_mem_win = {addr: mem[addr] for addr, _ in window}
        saved_a, saved_d, saved_len = a, d, len(ops_out)

        try:
            if use_domino:
                for _ in range(4):
                    to_flip = [
                        addr for addr, targ_v in sorted(window)
                        if find_a_for_crazy(mem[addr], targ_v) is None
                    ]
                    if not to_flip:
                        break
                    sweep = [CH_ROT, CH_DLD, CH_DLD]
                    cur_pos = base_dest + 1
                    for addr in to_flip:
                        sweep.append(CH_NOP * (addr - cur_pos))
                        sweep.append(CH_CRZ)
                        cur_pos = addr + 1
                    sim_ops("".join(sweep))
                    ret_s = return_to_82_from(to_flip[-1], mem)
                    sim_ops(ret_s)
                    assert d == 82

            remaining = [(addr, targ_v) for addr, targ_v in window if mem[addr] != targ_v]
            while remaining:
                scored: list[tuple[int, int, str]] = []
                for i_rem, (addr, targ_v) in enumerate(remaining):
                    seq = best_write_seq_for_addr(addr, base_dest, targ_v)
                    penalty = 0
                    if respect_81 and mem[addr] == 81 and targ_v != 81:
                        for u_addr, u_targ in remaining:
                            if u_addr < addr:
                                r = u_addr + 1
                                while r < 59049 and mem[r] != 81:
                                    r += 1
                                if r == addr:
                                    mult = 2 if find_a_for_crazy(mem[u_addr], u_targ) is None else 1
                                    penalty += 2 * mult
                    scored.append((len(seq) + penalty, i_rem, seq))
                # Deterministic by default: sorting is stable, so the first minimum
                # wins exactly as the previous strict-less-than scan did.  With an
                # explicit rng the search sometimes takes a slightly worse move, which
                # lets a caller run seeded restarts and keep the shortest preamble.
                scored.sort(key=lambda row: row[0])
                if rng is None or len(scored) == 1 or rng.random() < restart_p1:
                    _best_score, best_i, best_seq = scored[0]
                elif len(scored) == 2 or rng.random() < restart_p2:
                    _best_score, best_i, best_seq = scored[1]
                else:
                    _best_score, best_i, best_seq = scored[2]
                addr, targ_v = remaining.pop(best_i)
                assert best_seq is not None
                sim_ops(best_seq)
                assert d == 82 and mem[addr] == targ_v

            res_ops = "".join(ops_out[saved_len:])
        finally:
            mem[30:99] = saved_mem_low
            for addr, v in saved_mem_win.items():
                mem[addr] = v
            a = saved_a
            d = saved_d
            del ops_out[saved_len:]

        return res_ops

    base_dest = mem[94]
    sorted_addrs = sorted(high_mods.keys())
    idx = 0
    while idx < len(sorted_addrs):
        addr0 = sorted_addrs[idx]
        while addr0 - base_dest > 9:
            if addr0 - base_dest >= direct_gap:
                set_dest_94_direct(addr0 - 1)
                base_dest = mem[94]
            else:
                set_dest_94_direct(base_dest + 9)
                base_dest = mem[94]

        w9 = []
        idx9 = idx
        while idx9 < len(sorted_addrs):
            a_cand = sorted_addrs[idx9]
            if a_cand - base_dest > 9:
                break
            orig_v = high_mods[a_cand]
            targ_v = orig_v - delta if (lin_end < orig_v < n) else orig_v
            if mem[a_cand] != targ_v:
                w9.append((a_cand, targ_v))
            idx9 += 1

        if w9:
            best_w9 = None
            for use_dom in (False, True):
                for resp_81 in (False, True):
                    cand_w = run_window_strategy(w9, use_domino=use_dom, respect_81=resp_81)
                    if best_w9 is None or len(cand_w) < len(best_w9):
                        best_w9 = cand_w
            assert best_w9 is not None
            sim_ops(best_w9)
            for addr, targ_v in w9:
                assert mem[addr] == targ_v
        idx = idx9

    target_94 = handoff_d - 1
    curr_94 = mem[94]
    a_req = find_a_for_crazy(curr_94, target_94)
    if a_req is None:
        sim_ops(RESET_94_SEQ)
        curr_94 = C29524
        a_req = find_a_for_crazy(curr_94, target_94)
        assert a_req is not None

    sp_ops = solve_sp(a, mem[71 + 2], mem[71 + 3], a_req)
    sim_ops(CH_NOP * 3 + CH_DLD + sp_ops + CH_CRZ + CH_DLD + CH_NOP * 6 + CH_DLD)
    assert d == handoff_d
    ops_out.append(CH_JMP)
    return ops_out


def assemble_shifted_program(
    template_clean: list[int],
    ops: list[str],
    clean: list[int],
    lin_end: int,
    delta: int,
) -> tuple[bytes | None, int]:
    """Encode ``ops`` after the 99-cell template, pad with NOPs, append the shifted suffix.

    Returns ``(program_bytes, end_c)``; ``program_bytes`` is ``None`` when the encoded
    preamble would overrun the shifted handoff cell.
    """
    end_c = 99 + len(ops) - 1
    target_lin_end = lin_end - delta
    if end_c > target_lin_end:
        return None, end_c
    pad_len = target_lin_end - end_c
    out_bytes = bytearray(template_clean[:99])
    for idx, ch in enumerate(ops):
        c_pos = 99 + idx
        out_bytes.append(33 + ((XLAT1.index(ch) - c_pos) % 94))
    for idx in range(pad_len):
        c_pos = end_c + 1 + idx
        out_bytes.append(33 + ((XLAT1.index(CH_NOP) - c_pos) % 94))
    assert len(out_bytes) == target_lin_end + 1
    out_bytes.extend(clean[lin_end + 1:])
    return bytes(out_bytes), end_c


def build_compressed_program(
    prog_path: Path,
    lin_end: int,
    template_path: Path | None = None,
) -> tuple[bytes, dict]:
    t0 = time.time()
    clean, high_mods, handoff_d, handoff_c_target = extract_target_state(prog_path, lin_end)
    n = len(clean)

    if template_path is None:
        template_path = REPO_ROOT / "reference" / "malbolge_org" / "cat.mal"
    template_raw = template_path.read_bytes()
    template_clean = [b for b in template_raw if 33 <= b <= 126]

    ops0 = synthesize_preamble_ops(clean, high_mods, handoff_d, lin_end, delta=0, template_clean=template_clean)
    est_end = 99 + len(ops0) - 1
    max_k = (lin_end - est_end) // 94

    best_raw = None
    best_info = None
    for k in range(max_k + 15, 0, -1):
        delta = 94 * k
        ops = synthesize_preamble_ops(clean, high_mods, handoff_d, lin_end, delta=delta, template_clean=template_clean)
        cand_raw, end_c = assemble_shifted_program(template_clean, ops, clean, lin_end, delta)
        if cand_raw is None:
            continue
        pad_len = (lin_end - delta) - end_c
        if best_raw is None or len(cand_raw) < len(best_raw):
            best_raw = cand_raw
            best_info = {
                "orig_chars": n,
                "new_chars": len(cand_raw),
                "saved_chars": n - len(cand_raw),
                "saved_pct": round((n - len(cand_raw)) / n * 100.0, 2),
                "k": k,
                "delta": delta,
                "end_c": end_c,
                "pad_len": pad_len,
                "elapsed_s": round(time.time() - t0, 3),
            }
        break

    assert best_raw is not None and best_info is not None
    return best_raw, best_info


TARGETS = {
    "cat": ("cat.mal", 9003, "cat_compressed.mal"),
    "digital_root": ("digital_root.mal", 31802, "digital_root_compressed.mal"),
    "adder": ("adder.mal", 55802, "adder_compressed.mal"),
    "99_bottles": ("99_bottles.mal", 22044, "99_bottles_compressed.mal"),
}


def run_target(name: str, check: bool = False, output_dir: Path | None = None) -> None:
    from tools.test_compressed import verify_target
    src_file, lin_end, out_file = TARGETS[name]
    prog_path = REPO_ROOT / "reference" / "malbolge_org" / src_file
    out_path = (output_dir or REPO_ROOT / "artifacts") / out_file
    print(f"Compressing {name} (handoff {lin_end})", flush=True)
    raw_prog, info = build_compressed_program(prog_path, lin_end)
    # Generated candidates are verified before touching any published artifact.
    with tempfile.TemporaryDirectory(prefix="bolgeforge-verify-") as directory:
        candidate = Path(directory) / out_file
        candidate.write_bytes(raw_prog)
        count = verify_target(name, candidate)
    if check:
        if out_path.read_bytes() != raw_prog:
            raise RuntimeError(f"Rebuild differs from {out_file}; published file left intact")
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # Same-directory temporary file ensures readers only see complete artifacts.
        with tempfile.NamedTemporaryFile(dir=out_path.parent, prefix=".verified-", delete=False) as staged:
            staged.write(raw_prog)
            staged_path = Path(staged.name)
        staged_path.replace(out_path)
    print(f"PASS {name}: {count} cases; {'byte-exact rebuild' if check else 'published after verification'}; {info}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('targets', nargs='*', default=['cat'], choices=[*TARGETS, 'all'])
    parser.add_argument('--check', action='store_true', help='Verify deterministic reconstruction without changing artifacts')
    parser.add_argument('--output-dir', type=Path, help='Publish verified artifacts to another directory')
    args = parser.parse_args()
    targets = list(TARGETS) if 'all' in args.targets else args.targets
    for target in targets:
        run_target(target, args.check, args.output_dir)


if __name__ == "__main__":
    main()
