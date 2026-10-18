#!/usr/bin/env python3
"""tools/test_three_stage_clean.py - 3-Stage Clean Multi-Byte Cat on mb_ref.

Verifies:
- Battery 1: Empty stdin -> rc=0, 0 bytes emitted.
- Battery 2: All 256 single-byte values -> rc=0, bit-exact.
- Battery 2+: Two-byte corner cases -> rc=0, bit-exact.
- Battery 3: Three-byte corner cases and binary payloads -> rc=0, bit-exact.
"""
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.test_twostage_ab import assemble
from tools.trace_tm import op, rot, XLAT1, XLAT2

MB_REF = (REPO_ROOT / 'mb_ref') if (REPO_ROOT / 'mb_ref').exists() else (REPO_ROOT / 'oracle' / 'mb_ref')

def char_for(instr, c):
    idx = XLAT1.index(instr)
    return ((idx - (c % 94) + 94) % 94) + 33

def assemble_three_stage():
    N = 3380
    prog = [ord('o')] * N

    # Base 2-stage program (cells 0..1150)
    base = list(assemble())
    for i in range(len(base)):
        prog[i] = base[i]

    # Relocate Stage 2 discriminator data from 71..76 to BASE=77:
    prog[66] = 77
    prog[77] = 77
    prog[78] = ord('P') # 80: Y1
    prog[79] = 77       # pointer for rot
    prog[80] = ord('3') # 51: Y2
    prog[81] = 63       # pointer for j at cell 1105 to make d=64
    prog[82] = 79       # pointer for j at cell 465 to make d=80

    # Clear old 71..76 to avoid collisions:
    for i in range(71, 77):
        prog[i] = ord('o')

    # In Stage 2, loop back to 98 (lands on 99: Stage 1 Pass 2):
    prog[89] = 98

    # In Stage 1 on Pass 2:
    # c=117 is 'i', reads mem[86]. Set mem[86] = 121 -> lands on 122!
    prog[86] = 121

    # Stage 3 EOF HALT cell at 72..73:
    prog[72] = ord('o')          # sacrificial landing cushion
    prog[73] = char_for('v', 73) # HALT on Stage 3 EOF!

    # Stage 3 Discriminator Data:
    prog[87] = 91       # pointer for j at cell 122 to make d=92
    prog[91] = 91       # pointer to make d=92
    prog[92] = ord('y') # 121: W3 storage cell
    prog[93] = 91       # pointer for j during 10 rotations to make d=92
    prog[94] = ord('P') # 80: Y1 constant
    prog[95] = 93       # pointer during 2 rotations to make d=94
    prog[96] = 73       # pointer for j at cell 131 to make d=74
    prog[74] = ord('H') # 72: Y2 constant (produces 72 on EOF, 3312 on byte)
    prog[75] = 73       # pointer for j at cell 133 to make d=74
    prog[76] = 91       # pointer for j at cell 3314 to make d=92!

    # Stage 3 Output routing data:
    prog[97] = 83       # pointer for j after 10 rotations to make d=84
    prog[84] = 59       # pointer for j to make d=60
    prog[60] = ord('y') # 121: recovery constant for byte 3!
    prog[61] = 42       # jump target to halt (cell 42 lands on 43: HALT)
    prog[62] = 60       # pointer for j to make d=61

    # Discriminator for Stage 3 at cells 122..134:
    prog[121] = ord('o')           # landing cushion for jump from 117 (lands on 122!)
    prog[122] = char_for('j', 122) # d was 86+1=87. mem[87]=91 -> d+1 = 92
    prog[123] = char_for('p', 123) # crazy with mem[92] (121) -> mem[92] = W3. d becomes 93
    prog[124] = char_for('o', 124) # NOP -> d becomes 94
    prog[125] = char_for('p', 125) # crazy with mem[94] (80) -> op(W3, 80). d becomes 95

    # 2 Rotations on cell 94:
    prog[126] = char_for('j', 126) # d = mem[95] (93) -> d+1 = 94
    prog[127] = char_for('*', 127) # rot 1. d becomes 95
    prog[128] = char_for('j', 128) # d = mem[95] (93) -> d+1 = 94
    prog[129] = char_for('*', 129) # rot 2. d becomes 95

    prog[130] = char_for('o', 130) # NOP -> d becomes 96
    prog[131] = char_for('j', 131) # d = mem[96] (73) -> d+1 = 74 (Y2)
    prog[132] = char_for('p', 132) # crazy with mem[74] (72) -> 72 (EOF) or 3312 (byte). d becomes 75
    prog[133] = char_for('j', 133) # d = mem[75] (73) -> d+1 = 74
    prog[134] = char_for('i', 134) # jump to mem[74] (72 on EOF, 3312 on byte)!

    # Output Routine for Stage 3 at cells 3312..3344:
    prog[3312] = ord('o')           # landing cushion for jump 3312
    # At cell 3313: d is 75!
    prog[3313] = char_for('o', 3313) # NOP -> d becomes 76!
    prog[3314] = char_for('j', 3314) # d = mem[76] (91) -> d+1 = 92 (W3 storage)!

    # 10 Rotations on cell 92:
    c3 = 3315
    for i in range(10):
        prog[c3] = char_for('*', c3)     # rot on cell 92. d becomes 93
        c3 += 1
        if i < 9:
            prog[c3] = char_for('j', c3) # d = mem[93] (91) -> d+1 = 92
            c3 += 1

    # After 10th rot: d is 93.
    # NOPs to reach cell 97:
    prog[c3]   = char_for('o', c3)   # d becomes 94
    prog[c3+1] = char_for('o', c3+1) # d becomes 95
    prog[c3+2] = char_for('o', c3+2) # d becomes 96
    prog[c3+3] = char_for('o', c3+3) # d becomes 97
    c3 += 4

    # At cell c3: d is 97!
    prog[c3]   = char_for('j', c3)   # d = mem[97] (83) -> d+1 = 84!
    c3 += 1
    prog[c3]   = char_for('j', c3)   # d = mem[84] (59) -> d+1 = 60!
    c3 += 1
    prog[c3]   = char_for('p', c3)   # a = x3! d becomes 61!
    c3 += 1
    prog[c3]   = char_for('<', c3)   # prints byte x3! d becomes 62!
    c3 += 1
    prog[c3]   = char_for('j', c3)   # d = mem[62] (60) -> d+1 = 61!
    c3 += 1
    prog[c3]   = char_for('i', c3)   # jump to mem[61] (42) -> lands on 43 (HALT)!
    c3 += 1

    for idx, ch in enumerate(prog):
        assert 33 <= ch <= 126, f'Invalid byte at {idx}: {ch}'

    return bytes(prog)

if __name__ == '__main__':
    code = assemble_three_stage()
    out_file = REPO_ROOT / 'artifacts' / 'cand_three_stage_clean.mal'
    out_file.write_bytes(code)
    print(f'Assembled 3-stage candidate ({len(code)} bytes) to {out_file}')

    # Battery 1: Empty input
    p = subprocess.run([str(MB_REF), str(out_file)], input=b'', capture_output=True)
    assert p.returncode == 0 and p.stdout == b'', f'Battery 1 failed: {p}'
    print('Battery 1 (Empty stdin) [PASS]')

    # Battery 2: All 256 single bytes
    for b in range(256):
        payload = bytes([b])
        p = subprocess.run([str(MB_REF), str(out_file)], input=payload, capture_output=True)
        assert p.returncode == 0 and p.stdout == payload, f'Battery 2 failed on {b}: {p}'
    print('Battery 2 (All 256 single bytes) [PASS]')

    # Battery 2+: Two-byte corner cases
    two_byte_samples = [
        b'AB', b'hi', b'12', b'\n\n', b'\x00\x00', b'\xff\xff',
        bytes([0, 255]), bytes([255, 0]), bytes([127, 128]), bytes([65, 0]), bytes([0, 65])
    ]
    for payload in two_byte_samples:
        p = subprocess.run([str(MB_REF), str(out_file)], input=payload, capture_output=True)
        assert p.returncode == 0 and p.stdout == payload, f'Battery 2+ failed on {payload!r}: {p}'
    print('Battery 2+ (Two-byte corner cases) [PASS]')

    # Battery 3: Three-byte corner cases and binary permutations
    three_byte_samples = [
        b'ABC', b'xyz', b'123', b'Foo', b'Bar', b'cat', b'\r\n\x00',
        bytes([0, 0, 0]), bytes([255, 255, 255]), bytes([0, 128, 255]),
        bytes([255, 128, 0]), bytes([0, 255, 0]), bytes([255, 0, 255]),
        bytes([1, 2, 3]), bytes([254, 255, 0]), bytes([0, 1, 0])
    ]
    for payload in three_byte_samples:
        p = subprocess.run([str(MB_REF), str(out_file)], input=payload, capture_output=True)
        assert p.returncode == 0 and p.stdout == payload, f'Battery 3 failed on {payload!r}: {p}'
    print('Battery 3 (Three-byte corner cases & binary permutations) [PASS]')

    print('\n>>> EXTRAORDINARY SUCCESS: ALL 3-STAGE TESTS PASS 100% BIT-FOR-BIT ON mb_ref!')
