#!/usr/bin/env python3
"""tools/test_twostage_ab.py - 2-Stage Multi-Byte Cat on mb_ref."""
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

def assemble():
    N = 1150
    prog = [ord('o')] * N

    # Cell 0: portal jump 'i' (char 'b') -> jumps to 98, lands on 99
    prog[0] = ord('b')

    # Common cells:
    prog[1] = ord('o')
    prog[2] = 35       # '#' pointer for j at 100 to make d = 36
    
    # EOF HALT cells:
    prog[8]  = ord('o') # sacrificial jump target for Stage 1 EOF (lands on 9)
    prog[9]  = char_for('v', 9) # HALT on Stage 1 EOF!
    prog[24] = ord('o') # sacrificial jump target for Stage 2 EOF (lands on 25)
    prog[25] = char_for('v', 25) # HALT on Stage 2 EOF!
    prog[42] = ord('o') # sacrificial jump target for post-Stage 2 HALT (lands on 43)
    prog[43] = char_for('v', 43) # HALT at cell 43!

    # =========================================================
    # STAGE 1 DATA CELLS (cells 35..58)
    # =========================================================
    prog[35] = 35       # '#' pointer to make d = 36
    prog[36] = ord('y') # 121: involution constant (stores W1)
    prog[37] = 35       # '#' pointer for j to make d = 36 during 10 rotations
    prog[38] = 47       # '/' pointer for j at 103 to make d = 48
    
    prog[47] = 47       # '/' pointer to make d = 48
    prog[48] = ord('P') # 80: Y1 constant
    prog[49] = 47       # '/' pointer for j to make d = 48 during 4 rotations
    prog[50] = ord('#') # 35: Y2 constant for Stage 1 (produces 8 on EOF, 368 on byte)
    
    prog[51] = 35       # '#' pointer for j at cell 369 to make d = 36
    prog[52] = 49       # '1' pointer for j at cell 116 to make d = 50
    
    prog[39] = 55       # '7' pointer to make d = 56
    prog[56] = ord('y') # 121: recovery constant for x1
    prog[58] = 63       # pointer to make d = 64 (Stage 2 storage)

    # Stage 1 Discriminator (cells 99..117):
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

    # Stage 1 Output Routine (cells 368..394):
    prog[368] = ord('o')           # sacrificial landing target for jump 368
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
    prog[39]  = 55                 # pointer at cell 39 to make d = 56
    prog[c+2] = char_for('j', c+2) # d = mem[39] (55) -> d+1 = 56!
    c += 3
    
    prog[c] = char_for('p', c)     # a = x1! d becomes 57
    c += 1
    prog[c] = char_for('<', c)     # prints byte x1! d becomes 58
    c += 1
    
    # At cell 394: d is 58.
    # At cell 394: j reads mem[58] (63) -> d+1 = 64 (points to Stage 2 storage cell 64)!
    prog[c] = char_for('j', c)     # d = mem[58] (63) -> d+1 = 64!
    c += 1
    
    # Now walk forward to cell 450 where Stage 2 Discriminator begins:
    while c < 450:
        prog[c] = char_for('o', c)
        c += 1
    # At cell 450:
    # Steps from 395 to 450 = 55 steps.
    # d was 64 at 394. At 450: d = 64 + 55 = 119!

    # =========================================================
    # STAGE 2 DATA CELLS (cells 63..95)
    # =========================================================
    prog[119] = 63      # pointer for j at cell 451 to make d = 64!
    prog[120] = 63      # pointer to make d = 64
    prog[63]  = 63      # pointer to make d = 64
    prog[64]  = ord('y') # 121: Stage 2 storage cell (W2)
    prog[65]  = 63      # pointer for j during 10 rotations
    prog[66]  = 71      # pointer to make d = 72 (Y1)
    
    prog[71] = 71       # pointer to make d = 72
    prog[72] = ord('P') # 80: Y1 constant
    prog[73] = 71       # pointer during 3 rotations
    prog[74] = ord('3') # 51: Y2 constant for Stage 2 (produces 24 on EOF, 1104 on byte)
    
    prog[75] = 63       # pointer for j at cell 1105 to make d = 64
    prog[76] = 73       # pointer for j at cell 465 to make d = 74
    
    prog[67] = 87       # pointer to make d = 88
    prog[88] = ord('y') # 121: recovery constant for x2
    prog[89] = 42       # jump target to cell 42 (lands on 43: HALT!)
    prog[90] = 88       # pointer for j to make d = 89

    # =========================================================
    # STAGE 2 DISCRIMINATOR (cells 450..466, k=3 rotations!)
    # =========================================================
    prog[450] = char_for('/', 450) # in -> a = x2! d was 119, becomes 120.
    prog[451] = char_for('j', 451) # d = mem[120] (63) -> d+1 = 64
    prog[452] = char_for('p', 452) # crazy with mem[64] (121) -> mem[64] = W2. d becomes 65!
    prog[453] = char_for('o', 453) # NOP -> d becomes 66
    prog[454] = char_for('j', 454) # d = mem[66] (71) -> d+1 = 72
    prog[455] = char_for('p', 455) # crazy with mem[72] (80) -> op(W2, 80). d becomes 73
    
    # 3 Rotations on cell 72 (since k=3 for Y2='3'):
    prog[456] = char_for('j', 456) # d = mem[73] (71) -> d+1 = 72
    prog[457] = char_for('*', 457) # rot 1. d becomes 73
    prog[458] = char_for('j', 458) # d = mem[73] (71) -> d+1 = 72
    prog[459] = char_for('*', 459) # rot 2. d becomes 73
    prog[460] = char_for('j', 460) # d = mem[73] (71) -> d+1 = 72
    prog[461] = char_for('*', 461) # rot 3. d becomes 73
    
    prog[462] = char_for('o', 462) # NOP -> d becomes 74
    prog[463] = char_for('p', 463) # crazy with mem[74] (51) -> 24 (EOF) or 1104 (byte). d becomes 75
    prog[464] = char_for('o', 464) # NOP -> d becomes 76
    prog[465] = char_for('j', 465) # d = mem[76] (73) -> d+1 = 74
    prog[466] = char_for('i', 466) # jump to mem[74] (24 on EOF, 1104 on byte)!

    # =========================================================
    # STAGE 2 OUTPUT ROUTINE (cells 1104..1135)
    # =========================================================
    # Target 1104 lands on 1105!
    prog[1104] = ord('o')           # sacrificial landing target for jump 1104!
    # At cell 1105: d is 75!
    prog[1105] = char_for('j', 1105) # d = mem[75] (63) -> d+1 = 64
    
    # 10 Rotations on cell 64:
    c2 = 1106
    for i in range(10):
        prog[c2] = char_for('*', c2)     # rot on cell 64. d becomes 65
        c2 += 1
        if i < 9:
            prog[c2] = char_for('j', c2) # d = mem[65] (63) -> d+1 = 64
            c2 += 1

    # After 10th rot: d is 65.
    prog[c2]   = char_for('o', c2)   # d becomes 66
    prog[c2+1] = char_for('o', c2+1) # d becomes 67
    prog[c2+2] = char_for('j', c2+2) # d = mem[67] (87) -> d+1 = 88!
    c2 += 3
    
    prog[c2] = char_for('p', c2)     # a = x2! d becomes 89
    c2 += 1
    prog[c2] = char_for('<', c2)     # prints byte x2! d becomes 90
    c2 += 1
    
    # Halt after printing byte 2:
    prog[c2] = char_for('j', c2)     # d = mem[90] (88) -> d+1 = 89 (points to 89, mem[89]=42)
    c2 += 1
    prog[c2] = char_for('i', c2)     # jump to mem[89] (42) -> lands on 43 (HALT)!
    c2 += 1

    print(f"Assembly complete. Stage 1 at 99..394, Stage 2 at 450..466, Output 2 at 1105..{c2}. N={N}")
    for idx, ch in enumerate(prog):
        assert 33 <= ch <= 126, f"Byte at {idx} invalid: {ch}"
    return bytes(prog)

code = assemble()
out_file = REPO_ROOT / 'artifacts' / 'cand_two_stage.mal'
out_file.write_bytes(code)
print(f"Assembled {len(code)} bytes to {out_file}")

# Battery 1: Empty input
p0 = subprocess.run([str(MB_REF), str(out_file)], input=b'', capture_output=True)
print(f"Empty stdin: rc={p0.returncode}, stdout={p0.stdout!r}")
assert p0.returncode == 0 and p0.stdout == b""

# Battery 2: Single char 'A'
p1 = subprocess.run([str(MB_REF), str(out_file)], input=b'A', capture_output=True)
print(f"Input 'A': rc={p1.returncode}, stdout={p1.stdout!r}")
assert p1.returncode == 0 and p1.stdout == b"A"

# Battery 3: Two chars 'AB'
p2 = subprocess.run([str(MB_REF), str(out_file)], input=b'AB', capture_output=True)
print(f"Input 'AB': rc={p2.returncode}, stdout={p2.stdout!r}")
assert p2.returncode == 0 and p2.stdout == b"AB"
print("\n>>> EXTRAORDINARY SUCCESS: BOTH 'A' AND 'AB' ECHOED 100% BIT-FOR-BIT ON mb_ref!")
