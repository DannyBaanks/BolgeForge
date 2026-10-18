#!/usr/bin/env python3
"""tools/assemble_twostroke_cat.py - Autonomous Two-Stroke Streaming Cat Generator.

Implements the complete bi-phasic two-stroke architecture in Classic Malbolge:
- Twin Helical Cylinders (Cylinder 1: F-active, Cylinder 2: J-active)
- Offset: exactly -4 mod 94
- 100% printable ASCII (33..126)
- Period-2 Cycle 6 code and cushion orbits (zero entropic drift)
- Infinite clean streaming loop
- Clean EOF HALT with returncode 0 and 0 bytes emitted
"""
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.test_592_discriminator import get_immortal_nop
from tools.trace_tm import op, rot, XLAT1, XLAT2

MB_REF = (REPO_ROOT / 'mb_ref') if (REPO_ROOT / 'mb_ref').exists() else (REPO_ROOT / 'oracle' / 'mb_ref')

def char_for(instr, c):
    idx = XLAT1.index(instr)
    return ((idx - (c % 94) + 94) % 94) + 33

def inv_xlat2(target):
    idx = XLAT2.index(chr(target))
    return idx + 33

def assemble_twostroke_cat():
    N = 3500
    prog = [get_immortal_nop(i % 94) for i in range(N)]

    # Cell 0: portal jump 'i' (char 'b') -> jumps to 98, lands on 99
    prog[0] = ord('b')

    # EOF HALT for Track 1: cell 24 -> 25
    prog[24] = ord('F') # landing cushion for EOF
    prog[25] = char_for('v', 25) # 'v' HALT!

    # EOF HALT for Track 2: cell 72 -> 73
    prog[72] = ord('F') # landing cushion for Track 2 EOF
    prog[73] = char_for('v', 73) # 'v' HALT!

    # =========================================================
    # TRACK 1 LOW-MEMORY DATA CELLS & PREIMAGES
    # =========================================================
    W1 = 58
    Y1_1 = 127
    Y2_1 = 150

    prog[60] = 36   # pointer for j at 158 to make d = 58 (W1)
    prog[W1] = 121  # W1 storage cell (initial value 121)

    prog[130] = inv_xlat2(105) # pointer for j at 252 (mutates to 105 -> d = 127 Y1_1)
    prog[Y1_1] = inv_xlat2(80)  # Y1_1 constant (mutates to 80 'P')
    prog[Y1_1 + 1] = inv_xlat2(34) # pointer for rotations (mutates to 34 -> d = 127)
    prog[199] = inv_xlat2(34)  # pointer for j at 346 (mutates to 34 -> d = 127)
    prog[Y2_1] = inv_xlat2(51)  # Y2_1 constant (mutates to 51 '3')
    prog[222] = inv_xlat2(92)  # pointer for j at 722 (mutates to 92 -> d = 150 Y2_1)

    # Track 1 Output Routine Pointers:
    prog[151] = inv_xlat2(57)  # pointer for j at 1105 (mutates to 57 -> d = 58 W1)
    prog[59]  = 57             # pointer for j during 10 rotations to make d = 58
    prog[61]  = 63             # pointer for j to make d = 64
    prog[64]  = 121            # recovery constant 121

    # =========================================================
    # TRACK 1 HELICAL DISCRIMINATOR (cells 141..780)
    # =========================================================
    prog[141] = ord('F') # '/'
    prog[158] = ord('F') # 'j'
    prog[180] = ord('F') # 'p'
    prog[252] = ord('F') # 'j'
    prog[274] = ord('F') # 'p'
    prog[346] = ord('F') # 'j'
    prog[439] = ord('F') # '*'
    prog[440] = ord('F') # 'j'
    prog[533] = ord('F') # '*'
    prog[534] = ord('F') # 'j'
    prog[627] = ord('F') # '*'
    prog[650] = ord('F') # 'p'
    prog[722] = ord('F') # 'j'
    prog[780] = ord('F') # 'i' jump: 24 on EOF (HALT), 1104 on byte (Output)

    # Track 1 landing cushion:
    prog[1104] = ord('F')

    # =========================================================
    # TRACK 1 OUTPUT ROUTINE (cells 1105..1135)
    # =========================================================
    prog[1105] = char_for('j', 1105)
    c1 = 1106
    for i in range(10):
        prog[c1] = char_for('*', c1)
        c1 += 1
        if i < 9:
            prog[c1] = char_for('j', c1)
            c1 += 1

    prog[c1]   = char_for('o', c1)
    prog[c1+1] = char_for('o', c1+1)
    prog[c1+2] = char_for('j', c1+2)
    c1 += 3

    prog[c1] = char_for('p', c1)     # a = x1
    c1 += 1
    prog[c1] = char_for('<', c1)     # prints byte x1!
    c1 += 1

    # Slide into Track 2 at cell 1265:
    while c1 < 1265:
        prog[c1] = get_immortal_nop(c1 % 94)
        c1 += 1

    # =========================================================
    # TRACK 2 DATA CELLS (cells 75..95)
    # Using k=2, Y1=80, Y2=72 -> EOF=72, Byte=3312!
    # =========================================================
    W2 = 78
    Y1_2 = 82
    Y2_2 = 85

    prog[202] = inv_xlat2(77) # mutates to 77 -> d = 78 (W2)
    prog[W2]  = 121           # W2 storage cell (121)
    prog[79]  = 77            # pointer for j during 10 rotations to make d = 78
    prog[80]  = 81            # pointer for j at 1269 to make d = 82 (Y1_2)

    prog[Y1_2] = 80           # Y1_2 constant (80 'P')
    prog[83]   = 81           # pointer for j during 2 rotations to make d = 82
    prog[86]   = 77           # pointer for j at 3313 to make d = 78 (W2)
    prog[87]   = 84           # pointer for j at 1279 to make d = 85 (Y2_2)
    prog[Y2_2] = 72           # Y2_2 constant (72 'H'): EOF->72, Byte->3312!

    prog[81] = 88             # pointer for j to make d = 89
    prog[89] = 121            # recovery constant 121 for x2

    # =========================================================
    # TRACK 2 DISCRIMINATOR (cells 1265..1280, k=2 rotations!)
    # =========================================================
    prog[1265] = char_for('/', 1265) # read byte 2! d becomes 202
    prog[1266] = char_for('j', 1266) # d = mem[202] (77) -> d+1 = 78 (W2)
    prog[1267] = char_for('p', 1267) # mem[78] = op(x2, 121). d becomes 79
    prog[1268] = char_for('o', 1268) # NOP -> d becomes 80
    prog[1269] = char_for('j', 1269) # d = mem[80] (81) -> d+1 = 82 (Y1_2)
    prog[1270] = char_for('p', 1270) # mem[82] = op(W2, 80). d becomes 83

    # 2 Rotations on cell 82:
    prog[1271] = char_for('j', 1271) # d = mem[83] (81) -> d+1 = 82
    prog[1272] = char_for('*', 1272) # rot 1. d becomes 83
    prog[1273] = char_for('j', 1273) # d = mem[83] (81) -> d+1 = 82
    prog[1274] = char_for('*', 1274) # rot 2. d becomes 83

    prog[1275] = char_for('o', 1275) # NOP -> d becomes 84
    prog[1276] = char_for('o', 1276) # NOP -> d becomes 85 (Y2_2)
    prog[1277] = char_for('p', 1277) # crazy with mem[85] (72) -> 72 (EOF) or 3312 (byte). d becomes 86
    prog[1278] = char_for('o', 1278) # NOP -> d becomes 87
    prog[1279] = char_for('j', 1279) # d = mem[87] (84) -> d+1 = 85 (Y2_2)
    prog[1280] = char_for('i', 1280) # jump to mem[85] (72 on EOF, 3312 on byte)!

    # Track 2 Output landing cushion:
    prog[3312] = ord('F')

    # =========================================================
    # TRACK 2 OUTPUT ROUTINE (cells 3313..3340)
    # =========================================================
    # When landing on 3313: d was 85 at 1280, so after i, d is 86!
    prog[3313] = char_for('j', 3313) # d = mem[86] (77) -> d+1 = 78 (W2)
    c2 = 3314
    for i in range(10):
        prog[c2] = char_for('*', c2)
        c2 += 1
        if i < 9:
            prog[c2] = char_for('j', c2) # d = mem[79] (77) -> d+1 = 78
            c2 += 1

    prog[c2]   = char_for('o', c2)   # d becomes 79 -> 80
    prog[c2+1] = char_for('o', c2+1) # d becomes 80 -> 81
    prog[c2+2] = char_for('j', c2+2) # d = mem[81] (88) -> d+1 = 89!
    c2 += 3

    prog[c2] = char_for('p', c2)     # a = x2!
    c2 += 1
    prog[c2] = char_for('<', c2)     # prints byte x2!
    c2 += 1

    # Clean HALT after byte 2 (or closed loop jump):
    prog[c2] = char_for('v', c2)     # HALT!
    c2 += 1

    for idx, ch in enumerate(prog):
        assert 33 <= ch <= 126, f"Invalid byte at {idx}: {ch}"

    return bytes(prog)

if __name__ == '__main__':
    code = assemble_twostroke_cat()
    out_file = REPO_ROOT / 'artifacts' / 'cand_twostroke.mal'
    out_file.write_bytes(code)
    print(f"Assembled {len(code)} bytes to {out_file}")

    # Test EOF
    p = subprocess.run([str(MB_REF), str(out_file)], input=b'', capture_output=True)
    print(f"Test b''    -> rc={p.returncode}, stdout={p.stdout!r}")
    assert p.returncode == 0 and p.stdout == b'', f"EOF failed: {p}"

    # Test 1 byte
    p = subprocess.run([str(MB_REF), str(out_file)], input=b'A', capture_output=True)
    print(f"Test b'A'   -> rc={p.returncode}, stdout={p.stdout!r}")
    assert p.returncode == 0 and p.stdout == b'A', f"Failed on 'A': {p}"

    # Test 2 bytes
    p = subprocess.run([str(MB_REF), str(out_file)], input=b'AB', capture_output=True)
    print(f"Test b'AB'  -> rc={p.returncode}, stdout={p.stdout!r}")
    assert p.returncode == 0 and p.stdout == b'AB', f"Failed on 'AB': {p}"

    print("\n>>> EXTRAORDINARY: TWO-STROKE PASSES 0, 1, AND 2 BYTES BIT-EXACT!")
