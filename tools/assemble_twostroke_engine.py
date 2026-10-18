#!/usr/bin/env python3
"""tools/assemble_twostroke_engine.py - Complete Two-Stroke Period-2 MicroCat Generator.

Builds a self-regenerating bi-phasic Cat in Classic Malbolge:
- Cylinder 1: fires on odd bytes (F -> J), regenerates on even bytes (J -> F)
- Cylinder 2: regenerates on odd bytes (J -> F), fires on even bytes (F -> J)
- Closed loop: single permanent jump at end of track returns to Cylinder 1
- Zero entropic drift: 100% Period-2 conservation
"""
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.trace_tm import op, rot, XLAT1, XLAT2

MB_REF = (REPO_ROOT / 'mb_ref') if (REPO_ROOT / 'mb_ref').exists() else (REPO_ROOT / 'oracle' / 'mb_ref')

def char_for(instr, c):
    idx = XLAT1.index(instr)
    return ((idx - (c % 94) + 94) % 94) + 33

def assemble_twostroke():
    # Program size: 1200 bytes
    N = 1200
    prog = [ord('o')] * N

    # Cell 0: portal jump 'i' (char 'b') -> jumps to 98, lands on 99
    prog[0] = ord('b')

    # Common EOF HALT cells:
    prog[8]  = ord('o') # landing cushion for Track 1 EOF
    prog[9]  = char_for('v', 9) # HALT on Track 1 EOF!
    prog[24] = ord('o') # landing cushion for Track 2 EOF
    prog[25] = char_for('v', 25) # HALT on Track 2 EOF!

    # =========================================================
    # TRACK 1 DATA CELLS (cells 35..58)
    # =========================================================
    prog[1] = ord('o')
    prog[2] = 35        # pointer for j at 100 to make d = 36
    prog[35] = 35       # '#' pointer to make d = 36
    prog[36] = ord('y') # 121: Track 1 storage (W1)
    prog[37] = 35       # '#' pointer for j to make d = 36 during 10 rotations
    prog[38] = 47       # '/' pointer for j at 103 to make d = 48
    
    prog[47] = 47       # '/' pointer to make d = 48
    prog[48] = ord('P') # 80: Y1 constant
    prog[49] = 47       # '/' pointer for j to make d = 48 during 4 rotations
    prog[50] = ord('#') # 35: Y2 constant
    
    prog[51] = 35       # '#' pointer for j at cell 369 to make d = 36
    prog[52] = 49       # '1' pointer for j at cell 116 to make d = 50
    
    prog[39] = 55       # '7' pointer to make d = 56
    prog[56] = ord('y') # 121: recovery constant
    prog[58] = 63       # pointer to make d = 64 (Track 2 storage)

    # Track 1 Discriminator (cells 99..117):
    prog[99]  = char_for('/', 99)  # in -> a = x1. d was 1, becomes 2
    prog[100] = char_for('j', 100) # d = mem[2] (35) -> d+1 = 36
    prog[101] = char_for('p', 101) # crazy with mem[36] (121) -> mem[36] = W1. d becomes 37
    prog[102] = char_for('o', 102) # NOP -> d becomes 38
    prog[103] = char_for('j', 103) # d = mem[38] (47) -> d+1 = 48
    prog[104] = char_for('p', 104) # crazy with mem[48] (80) -> op(W1, 80). d becomes 49
    
    # 4 Rotations on cell 48:
    prog[105] = char_for('j', 105) # d = mem[49] (47) -> d+1 = 48
    prog[106] = char_for('*', 106) # rot 1. d becomes 49
    prog[107] = char_for('j', 107) # d = mem[49] (47) -> d+1 = 48
    prog[108] = char_for('*', 108) # rot 2. d becomes 49
    prog[109] = char_for('j', 109) # d = mem[49] (47) -> d+1 = 48
    prog[110] = char_for('*', 110) # rot 3. d becomes 49
    prog[111] = char_for('j', 111) # d = mem[49] (47) -> d+1 = 48
    prog[112] = char_for('*', 112) # rot 4. d becomes 49
    
    prog[113] = char_for('o', 113) # NOP -> d becomes 50
    prog[114] = char_for('p', 114) # crazy with mem[50] (35) -> 8 (EOF) or 368 (byte). d becomes 51
    prog[115] = char_for('o', 115) # NOP -> d becomes 52
    prog[116] = char_for('j', 116) # d = mem[52] (49) -> d+1 = 50
    prog[117] = char_for('i', 117) # jump to mem[50] (8 on EOF, 368 on byte)!

    # Track 1 Output Routine (cells 368..394):
    prog[368] = ord('o')           # landing cushion for jump 368
    prog[369] = char_for('j', 369) # d was 51. j reads mem[51] (35) -> d+1 = 36
    
    # 10 Rotations on cell 36:
    c = 370
    for i in range(10):
        prog[c] = char_for('*', c)     # rot on cell 36. d becomes 37
        c += 1
        if i < 9:
            prog[c] = char_for('j', c) # d = mem[37] (35) -> d+1 = 36
            c += 1

    prog[c]   = char_for('o', c)   # d becomes 38
    prog[c+1] = char_for('o', c+1) # d becomes 39
    prog[c+2] = char_for('j', c+2) # d = mem[39] (55) -> d+1 = 56!
    c += 3
    
    prog[c] = char_for('p', c)     # a = x1! d becomes 57
    c += 1
    prog[c] = char_for('<', c)     # prints byte x1! d becomes 58
    c += 1
    
    # At cell 394: d is 58. j reads mem[58] (63) -> d+1 = 64 (Track 2 storage)!
    prog[c] = char_for('j', c)
    c += 1
    
    while c < 450:
        prog[c] = char_for('o', c)
        c += 1
    
    # =========================================================
    # TRACK 2 DATA CELLS (cells 63..90)
    # =========================================================
    prog[119] = 63      # pointer for j at cell 451 to make d = 64
    prog[120] = 63      # pointer to make d = 64
    prog[63]  = 63      # pointer to make d = 64
    prog[64]  = ord('y') # 121: Track 2 storage (W2)
    prog[65]  = 63      # pointer for j during 10 rotations
    prog[66]  = 77      # pointer to make d = 78 (Y1)
    
    prog[77] = 77       # pointer to make d = 78
    prog[78] = ord('P') # 80: Y1 constant
    prog[79] = 77       # pointer during 3 rotations
    prog[80] = ord('3') # 51: Y2 constant
    
    prog[81] = 63       # pointer for j at cell 1105 to make d = 64
    prog[82] = 79       # pointer for j at cell 465 to make d = 80
    
    prog[67] = 87       # pointer to make d = 88
    prog[88] = ord('y') # 121: recovery constant for x2
    prog[89] = 98       # jump target to cell 98 (lands on 99 for Track 1!)
    prog[90] = 88       # pointer for j to make d = 89

    # Track 2 Discriminator (cells 450..466):
    prog[450] = char_for('/', 450) # in -> a = x2! d was 119, becomes 120.
    prog[451] = char_for('j', 451) # d = mem[120] (63) -> d+1 = 64
    prog[452] = char_for('p', 452) # crazy with mem[64] (121) -> mem[64] = W2. d becomes 65!
    prog[453] = char_for('o', 453) # NOP -> d becomes 66
    prog[454] = char_for('j', 454) # d = mem[66] (77) -> d+1 = 78
    prog[455] = char_for('p', 455) # crazy with mem[78] (80) -> op(W2, 80). d becomes 79
    
    # 3 Rotations on cell 78:
    prog[456] = char_for('j', 456) # d = mem[79] (77) -> d+1 = 78
    prog[457] = char_for('*', 457) # rot 1. d becomes 79
    prog[458] = char_for('j', 458) # d = mem[79] (77) -> d+1 = 78
    prog[459] = char_for('*', 459) # rot 2. d becomes 79
    prog[460] = char_for('j', 460) # d = mem[79] (77) -> d+1 = 78
    prog[461] = char_for('*', 461) # rot 3. d becomes 79
    
    prog[462] = char_for('o', 462) # NOP -> d becomes 80
    prog[463] = char_for('p', 463) # crazy with mem[80] (51) -> 24 (EOF) or 1104 (byte). d becomes 81
    prog[464] = char_for('o', 464) # NOP -> d becomes 82
    prog[465] = char_for('j', 465) # d = mem[82] (79) -> d+1 = 80
    prog[466] = char_for('i', 466) # jump to mem[80] (24 on EOF, 1104 on byte)!

    # Track 2 Output Routine (cells 1104..1135):
    prog[1104] = ord('o')           # landing cushion for jump 1104
    prog[1105] = char_for('j', 1105) # d was 81. j reads mem[81] (63) -> d+1 = 64
    
    # 10 Rotations on cell 64:
    c2 = 1106
    for i in range(10):
        prog[c2] = char_for('*', c2)     # rot on cell 64. d becomes 65
        c2 += 1
        if i < 9:
            prog[c2] = char_for('j', c2) # d = mem[65] (63) -> d+1 = 64
            c2 += 1

    prog[c2]   = char_for('o', c2)   # d becomes 66
    prog[c2+1] = char_for('o', c2+1) # d becomes 67
    prog[c2+2] = char_for('j', c2+2) # d = mem[67] (87) -> d+1 = 88!
    c2 += 3
    
    prog[c2] = char_for('p', c2)     # a = x2! d becomes 89
    c2 += 1
    prog[c2] = char_for('<', c2)     # prints byte x2! d becomes 90
    c2 += 1
    
    # Jump back to Track 1 (cell 98, landing on 99):
    prog[c2] = char_for('j', c2)     # d = mem[90] (88) -> d+1 = 89
    c2 += 1
    prog[c2] = char_for('i', c2)     # jump to mem[89] (98) -> lands on 99!
    c2 += 1

    for idx, ch in enumerate(prog):
        assert 33 <= ch <= 126, f"Byte at {idx} invalid: {ch}"
    return bytes(prog)

if __name__ == '__main__':
    code = assemble_twostroke()
    out_file = REPO_ROOT / 'artifacts' / 'cand_twostroke.mal'
    out_file.write_bytes(code)
    print(f"Assembled {len(code)} bytes to {out_file}")

    # Test suite
    test_cases = [b'', b'A', b'AB']
    for t in test_cases:
        p = subprocess.run([str(MB_REF), str(out_file)], input=t, capture_output=True)
        print(f"Test {t!r:6s} -> rc={p.returncode}, stdout={p.stdout!r}")
        assert p.returncode == 0 and p.stdout == t, f"Failed on {t}: got rc={p.returncode}, stdout={p.stdout!r}"
    print("\n>>> TWO-STROKE BASELINE VERIFIED FOR 0, 1, 2 BYTES!")

