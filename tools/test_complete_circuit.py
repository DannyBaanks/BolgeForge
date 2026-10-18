#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.trace_tm import op, rot, XLAT1, XLAT2

MB_REF = REPO_ROOT / 'mb_ref' if (REPO_ROOT / 'mb_ref').exists() else (REPO_ROOT / 'oracle' / 'mb_ref')

def char_for(instr, c):
    idx = XLAT1.index(instr)
    return ((idx - (c % 94) + 94) % 94) + 33

def build_program():
    N = 430
    prog = [ord('o')] * N

    # Cell 0: portal jump 'i' (char 'b') -> jumps to 98, lands on 99
    prog[0] = ord('b')

    # Data cells in low memory:
    prog[1] = ord('o')
    prog[2] = 35       # '#' pointer for j at 100 to make d = 36
    prog[8] = ord('o') # sacrificial jump target for EOF (lands on 9)
    prog[9] = char_for('v', 9) # HALT on EOF!

    # Storage and pointer cells:
    prog[35] = 35       # '#' pointer to make d = 36
    prog[36] = ord('y') # 121: involution constant (stores W)
    prog[37] = 35       # '#' pointer for j to make d = 36 during 10 rotations!
    prog[38] = 47       # '/' pointer for j at 103 to make d = 48
    
    # Discriminator constants:
    prog[47] = 47       # '/' pointer to make d = 48
    prog[48] = ord('P') # 80: Y1 constant
    prog[49] = 47       # '/' pointer for j to make d = 48 during 4 rotations
    prog[50] = ord('#') # 35: Y2 constant
    
    # Jump target pointers:
    prog[51] = 35       # '#' pointer for j at cell 369 to make d = 36!
    prog[52] = 49       # '1' pointer for j at cell 116 to make d = 50!
    
    # Recovery constants and return jump:
    prog[53] = 55       # '7' pointer to make d = 56
    prog[56] = ord('y') # 121: second involution constant for recovering b
    prog[57] = 98       # 'b' jump target to cell 98 (lands on 99)
    prog[58] = 56       # '8' pointer for j to make d = 57 (points to 57)

    # 1. Low-memory discriminator (cells 99..117):
    prog[99]  = char_for('/', 99)  # in -> a = x. d was 1, becomes 2
    prog[100] = char_for('j', 100) # d = mem[2] (35) -> d+1 = 36
    prog[101] = char_for('p', 101) # crazy with mem[36] (121) -> mem[36] = W. d becomes 37
    prog[102] = char_for('o', 102) # NOP -> d becomes 38
    prog[103] = char_for('j', 103) # d = mem[38] (47) -> d+1 = 48
    prog[104] = char_for('p', 104) # crazy with mem[48] (80) -> op(W, 80). d becomes 49
    
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

    # 2. Output routine starting at cell 369:
    prog[368] = ord('o')           # sacrificial landing target for jump 368!
    prog[369] = char_for('j', 369) # d was 51. j reads mem[51] (35) -> d+1 = 36!
    
    # 10 Rotations on cell 36:
    c = 370
    for i in range(10):
        prog[c] = char_for('*', c)     # rot on cell 36. d becomes 37
        c += 1
        if i < 9:
            prog[c] = char_for('j', c) # d = mem[37] (35) -> d+1 = 36
            c += 1

    # After 10th rotation: d is 37.
    # We want d to point to cell 56 (mem[56] = 121):
    # From 37:
    # Cell 37 had 35. What if we do:
    # prog[c] = char_for('o', c) -> d becomes 38
    # prog[c+1] = char_for('o', c+1) -> d becomes 39
    # prog[39] = 55 (pointer to 56)!
    # prog[c+2] = char_for('j', c+2) -> d = mem[39] (55) -> d+1 = 56!
    prog[39] = 55 # pointer to make d = 56
    prog[c]   = char_for('o', c)   # d becomes 38
    prog[c+1] = char_for('o', c+1) # d becomes 39
    prog[c+2] = char_for('j', c+2) # d = mem[39] (55) -> d+1 = 56!
    c += 3
    
    # At cell c: d is 56 (mem[56] = 121).
    # p computes a = mem[56] = op(a, 121) = b!
    prog[c] = char_for('p', c) # a = b! d becomes 57
    c += 1
    
    # Output byte:
    prog[c] = char_for('<', c) # prints byte! d becomes 58
    c += 1
    
    # Return jump:
    # At cell c, d is 58. prog[58] = 56 -> d+1 = 57 (points to 57).
    prog[c]   = char_for('j', c)   # d = mem[58] (56) -> d+1 = 57
    c += 1
    prog[c]   = char_for('i', c)   # jump to mem[57] (98) -> lands on 99!
    c += 1

    print(f"Total instructions placed up to cell {c}. N = {N}")
    for idx, ch in enumerate(prog):
        assert 33 <= ch <= 126, f"Byte at {idx} invalid: {ch}"
    return bytes(prog)

def test_sim(prog_bytes, input_data):
    mem = list(prog_bytes) + [0] * (59049 - len(prog_bytes))
    for i in range(len(prog_bytes), 59049):
        mem[i] = op(mem[i-1], mem[i-2])
    
    a = c = d = 0
    step = 0
    in_idx = 0
    out_buf = bytearray()
    
    while step < 1000:
        val = mem[c]
        if val < 33 or val > 126:
            instr = 'NOP'
        else:
            instr = XLAT1[(val - 33 + c) % 94]
            
        if instr == 'j': d = mem[d]
        elif instr == 'i': c = mem[d]
        elif instr == '*': a = mem[d] = mem[d]//3 + (mem[d]%3)*19683
        elif instr == 'p': a = mem[d] = op(a, mem[d])
        elif instr == '<': out_buf.append(a & 255)
        elif instr == '/':
            if in_idx < len(input_data):
                a = input_data[in_idx]
                in_idx += 1
            else:
                a = 59048
        elif instr == 'v':
            return 0, bytes(out_buf), step
            
        if 33 <= val <= 126:
            mem[c] = ord(XLAT2[val - 33])
        c = 0 if c == 59048 else c + 1
        d = 0 if d == 59048 else d + 1
        step += 1
        
    return 1, bytes(out_buf), step

code = build_program()
out_file = REPO_ROOT / "artifacts" / "microcat.mal"
out_file.write_bytes(code)
print(f"Written {len(code)} bytes to {out_file}")

# 1. Test Simulation on EOF:
rc, out, steps = test_sim(code, b"")
print(f"SIM EOF: rc={rc}, out={out!r}, steps={steps}")
assert rc == 0 and out == b""

# 2. Test Simulation on 'A':
rc, out, steps = test_sim(code, b"A")
print(f"SIM 'A': rc={rc}, out={out!r}, steps={steps}")

# 3. Test on mb_ref:
p_eof = subprocess.run([str(MB_REF), str(out_file)], input=b"", capture_output=True)
print(f"mb_ref EOF: rc={p_eof.returncode}, stdout={p_eof.stdout!r}")
assert p_eof.returncode == 0 and p_eof.stdout == b""
print("  >>> BATTERY 1 PASSED ON mb_ref!")

p_a = subprocess.run([str(MB_REF), str(out_file)], input=b"A", capture_output=True)
print(f"mb_ref 'A': rc={p_a.returncode}, stdout={p_a.stdout!r}")
