#!/usr/bin/env python3
"""tools/test_valid_ascii_cat.py - Verify 100% valid printable ASCII Micro-Cat on mb_ref."""
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

def assemble_ascii_microcat():
    N = 125
    prog = [ord('o')] * N

    # Ending ('!', 'U') makes cell 369 in crazy fill decode to 'v' (HALT)
    prog[N-2] = ord('!')
    prog[N-1] = ord('U')

    # Cell 0: portal jump 'i' (char 'b') -> jumps to 98, lands on 99
    prog[0] = ord('b')

    # Data cells and pointers (ALL in 33..126!):
    prog[1] = ord('o')
    prog[2] = 37       # '%' pointer for j to make d = 38
    prog[8] = ord('o') # sacrificial jump target for bytes (lands on 9)

    prog[37] = 37      # '%' pointer for j to make d = 38
    prog[38] = ord('P') # 80: Y1 constant
    prog[39] = 37      # '%' pointer for j to make d = 38
    prog[40] = ord('#') # 35: Y2 constant
    prog[41] = 39      # "'" pointer for j to make d = 40
    # Jump target pointer to 98 (at cell 42):
    prog[42] = 98      # 'b'
    prog[43] = 41      # pointer for j to make d = 42

    # Low-memory discriminator instructions (cells 99..114):
    prog[99]  = char_for('/', 99)  # in -> a = x. d was 1, becomes 2
    prog[100] = char_for('j', 100) # d = mem[2] (37) -> d+1 = 38
    prog[101] = char_for('p', 101) # crazy with mem[38] (80) -> op(x, 80). d becomes 39
    prog[102] = char_for('j', 102) # d = mem[39] (37) -> d+1 = 38
    prog[103] = char_for('*', 103) # rot mem[38] (rot 1). d becomes 39
    prog[104] = char_for('j', 104) # d = mem[39] (37) -> d+1 = 38
    prog[105] = char_for('*', 105) # rot mem[38] (rot 2). d becomes 39
    prog[106] = char_for('j', 106) # d = mem[39] (37) -> d+1 = 38
    prog[107] = char_for('*', 107) # rot mem[38] (rot 3). d becomes 39
    prog[108] = char_for('j', 108) # d = mem[39] (37) -> d+1 = 38
    prog[109] = char_for('*', 109) # rot mem[38] (rot 4). d becomes 39
    prog[110] = char_for('o', 110) # NOP -> d becomes 40 (pointing to mem[40] = 35)
    prog[111] = char_for('p', 111) # crazy with mem[40] (35) -> 368 (EOF) or 8 (byte). d becomes 41
    prog[112] = char_for('j', 112) # d = mem[41] (39) -> d+1 = 40
    prog[113] = char_for('i', 113) # jump to mem[40] (368 or 8)!

    # Output routine starting at cell 9:
    prog[9]  = char_for('<', 9)   # prints byte!
    prog[10] = char_for('j', 10)  # d = mem[43] (41) -> d+1 = 42
    prog[11] = char_for('i', 11)  # jump to mem[42] (98) -> lands on 99!

    # Verify all characters in 33..126:
    for idx, ch in enumerate(prog):
        assert 33 <= ch <= 126, f"Byte at {idx} is invalid: {ch} (0x{ch:02x})"

    return bytes(prog)

if __name__ == '__main__':
    code = assemble_ascii_microcat()
    out_file = REPO_ROOT / 'artifacts' / 'cand_valid.mal'
    out_file.write_bytes(code)
    print(f"Assembled 100% valid ASCII program: {len(code)} bytes.")
    print(f"Written to: {out_file}")

    # Test with mb_ref on empty input:
    p = subprocess.run([str(MB_REF), str(out_file)], input=b'', capture_output=True)
    print(f"mb_ref returncode: {p.returncode}")
    print(f"mb_ref stdout: {p.stdout!r}")
    print(f"mb_ref stderr: {p.stderr!r}")
    assert p.returncode == 0, f"Expected returncode 0, got {p.returncode}"
    assert p.stdout == b"", f"Expected empty output, got {p.stdout!r}"
    print("  [PASS] BATTERY 1 VERIFIED ON mb_ref: Immediate EOF cleanly halts with exit 0 and 0 bytes emitted!")
