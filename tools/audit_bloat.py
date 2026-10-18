#!/usr/bin/env python3
"""tools/audit_bloat.py - BolgeForge Exact Corpus Telemetry & Bloat Auditor.

Executes every canonical Malbolge program in reference/malbolge_org/ to completion
under Olmstead Classic semantics (via an on-the-fly C telemetry kernel derived from
oracle/mb_ref.c, with zero hardcoded estimates) and measures:
1. Total file bytes and non-whitespace program opcodes (n).
2. Linear preamble end (c address of first non-entry jump 'i') and first I/O step/address.
3. Exact memory cells modified by '*' / 'p' before first I/O (split into low < n and high >= n).
4. Exact distinct instruction addresses (c) executed after first I/O until 'v' HALT.
5. Total execution steps to clean HALT.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = REPO_ROOT / 'reference' / 'malbolge_org'

C_AUDIT_SRC = r"""
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

static const char xlat1[] = "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha";
static const char xlat2[] = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@";

static inline unsigned short op(unsigned short x, unsigned short y) {
    unsigned short i = 0;
    static const unsigned short p9[5] = { 1, 9, 81, 729, 6561 };
    static const unsigned short o[9][9] = {
        { 4, 3, 3, 1, 0, 0, 1, 0, 0 },
        { 4, 3, 5, 1, 0, 2, 1, 0, 2 },
        { 5, 5, 4, 2, 2, 1, 2, 2, 1 },
        { 4, 3, 3, 1, 0, 0, 7, 6, 6 },
        { 4, 3, 5, 1, 0, 2, 7, 6, 8 },
        { 5, 5, 4, 2, 2, 1, 8, 8, 7 },
        { 7, 6, 6, 7, 6, 6, 4, 3, 3 },
        { 7, 6, 8, 7, 6, 8, 4, 3, 5 },
        { 8, 8, 7, 8, 8, 7, 5, 5, 4 },
    };
    for (int j = 0; j < 5; j++)
        i += o[y / p9[j] % 9][x / p9[j] % 9] * p9[j];
    return i;
}

static unsigned short mem[59049];
static unsigned char d_mod_pre[59049];
static unsigned char post_c_exec[59049];

int main(int argc, char **argv) {
    if (argc < 3) return 1;
    const char *path = argv[1];
    const char *sample_in = argv[2];

    FILE *f = fopen(path, "rb");
    if (!f) return 1;
    unsigned int file_bytes = 0, prog_len = 0;
    int x;
    while ((x = fgetc(f)) != EOF) {
        file_bytes++;
        if (isspace(x)) continue;
        if (x < 33 || x > 126) continue;
        mem[prog_len++] = (unsigned short)x;
    }
    fclose(f);
    for (unsigned int i = prog_len; i < 59049; i++) {
        mem[i] = op(mem[i - 1], mem[i - 2]);
    }
    memset(d_mod_pre, 0, sizeof(d_mod_pre));
    memset(post_c_exec, 0, sizeof(post_c_exec));

    unsigned short a = 0, c = 0, d = 0;
    unsigned long long step = 0;
    unsigned long long linear_end_step = ~0ULL;
    unsigned short linear_end_c = 0;
    unsigned long long first_io_step = ~0ULL;
    unsigned short first_io_c = 0, first_io_d = 0, first_io_a = 0;
    char first_io_ch = '?';
    int in_pos = 0;
    int in_len = (int)strlen(sample_in);

    while (step < 80000000ULL) {
        if (mem[c] >= 33 && mem[c] <= 126) {
            char instr = xlat1[(mem[c] - 33 + c) % 94];
            if (step > 0 && instr == 'i' && linear_end_step == ~0ULL) {
                linear_end_step = step;
                linear_end_c = c;
            }
            if ((instr == '/' || instr == '<') && first_io_step == ~0ULL) {
                first_io_step = step;
                first_io_c = c;
                first_io_d = d;
                first_io_a = a;
                first_io_ch = instr;
            }
            if (first_io_step != ~0ULL) {
                post_c_exec[c] = 1;
            }
            if (instr == 'j') {
                d = mem[d];
            } else if (instr == 'i') {
                c = mem[d];
            } else if (instr == '*') {
                if (first_io_step == ~0ULL) d_mod_pre[d] = 1;
                a = mem[d] = mem[d] / 3 + (mem[d] % 3) * 19683;
            } else if (instr == 'p') {
                if (first_io_step == ~0ULL) d_mod_pre[d] = 1;
                a = mem[d] = op(a, mem[d]);
            } else if (instr == '/') {
                a = (in_pos < in_len) ? (unsigned char)sample_in[in_pos++] : 59048;
            } else if (instr == 'v') {
                break;
            }
            mem[c] = (unsigned short)xlat2[mem[c] - 33];
        }
        c = (c == 59048) ? 0 : c + 1;
        d = (d == 59048) ? 0 : d + 1;
        step++;
    }

    int d_mod_low = 0, d_mod_high = 0;
    for (unsigned int i = 0; i < 59049; i++) {
        if (d_mod_pre[i]) {
            if (i < prog_len) d_mod_low++;
            else d_mod_high++;
        }
    }
    int post_c_low = 0, post_c_high = 0;
    for (unsigned int i = 0; i < 59049; i++) {
        if (post_c_exec[i]) {
            if (i < prog_len) post_c_low++;
            else post_c_high++;
        }
    }

    if (linear_end_step == ~0ULL) {
        linear_end_step = first_io_step;
        linear_end_c = first_io_c;
    }

    printf("{\"file_bytes\": %u, \"opcodes\": %u, \"linear_end_c\": %u, \"linear_end_step\": %llu, "
           "\"first_io_ch\": \"%c\", \"first_io_c\": %u, \"first_io_d\": %u, \"first_io_a\": %u, "
           "\"first_io_step\": %llu, \"d_mod_low\": %d, \"d_mod_high\": %d, "
           "\"post_c_low\": %d, \"post_c_high\": %d, \"total_steps\": %llu}\n",
           file_bytes, prog_len, linear_end_c, linear_end_step,
           first_io_ch, first_io_c, first_io_d, first_io_a,
           first_io_step, d_mod_low, d_mod_high,
           post_c_low, post_c_high, step);
    return 0;
}
"""

SAMPLE_INPUTS = {
    "adder.mal": "123\n456\n",
    "cat.mal": "Hello\n",
    "digital_root.mal": "12345\n",
    "rot13.mal": "Hello\n",
}


def main():
    if not shutil.which("gcc"):
        print("Error: gcc is required to compile the C telemetry kernel.", file=sys.stderr)
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        bin_path = Path(tmpdir) / "bf_audit_kernel"
        subprocess.run(
            ["gcc", "-O3", "-x", "c", "-", "-o", str(bin_path)],
            input=C_AUDIT_SRC.encode("utf-8"),
            check=True,
        )

        print("=" * 112)
        print("BOLGEFORGE EXACT CORPUS TELEMETRY & BLOAT AUDIT (C ORACLE KERNEL, ZERO HARDCODES)")
        print("=" * 112)
        fmt = "%-16s | %7s | %7s | %10s | %12s | %14s | %12s | %11s"
        print(fmt % (
            "Program", "File B", "Opcodes", "Linear End", "First I/O",
            "D-Mod (L+H)", "Post-IO C", "Total Steps"
        ))
        print("-" * 112)

        progs = sorted(CORPUS_DIR.glob("*.mal"))
        for p in progs:
            sample = SAMPLE_INPUTS.get(p.name, "")
            out = subprocess.check_output([str(bin_path), str(p), sample]).decode("utf-8")
            d = json.loads(out)
            d_mod_tot = d["d_mod_low"] + d["d_mod_high"]
            post_c_tot = d["post_c_low"] + d["post_c_high"]
            lin_pct = (d["linear_end_c"] / d["opcodes"] * 100.0) if d["opcodes"] else 0.0
            print(fmt % (
                p.name,
                f"{d['file_bytes']:,}",
                f"{d['opcodes']:,}",
                f"{d['linear_end_c']:,} ({lin_pct:4.1f}%)",
                f"@{d['first_io_step']:,} ({d['first_io_ch']})",
                f"{d_mod_tot:4d} ({d['d_mod_low']}+{d['d_mod_high']})",
                f"{post_c_tot:3d} ({d['post_c_low']}+{d['post_c_high']})",
                f"{d['total_steps']:,}",
            ))
        print("=" * 112)


if __name__ == "__main__":
    main()
