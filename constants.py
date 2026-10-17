"""constants.py - Malbolge machine constants, translation tables and trit operations."""

MEM_SIZE = 3 ** 10  # 59,049 words

# Translation tables (Canonical 94 printable ASCII characters)
XLAT1 = (
    "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI"
    ".v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha"
)
XLAT2 = (
    "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1C"
    "B6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
)

assert len(XLAT1) == 94
assert len(XLAT2) == 94

# Normalized opcodes
OP_JMP = 4      # 'i' in xlat1
OP_OUT = 5      # '<' in xlat1
OP_IN = 23      # '/' in xlat1
OP_ROT = 39     # '*' in xlat1
OP_DLOAD = 40   # 'j' in xlat1
OP_CRAZY = 62   # 'p' in xlat1
OP_NOP = 68     # 'o' in xlat1
OP_END = 81     # 'v' in xlat1

OP_CHAR_MAP = {
    OP_JMP: "i",
    OP_OUT: "<",
    OP_IN: "/",
    OP_ROT: "*",
    OP_DLOAD: "j",
    OP_CRAZY: "p",
    OP_NOP: "o",
    OP_END: "v",
}

CHAR_OP_MAP = {v: k for k, v in OP_CHAR_MAP.items()}

# Cache indices of opcode characters in XLAT1
OP_XLAT1_INDEX = {op: XLAT1.index(ch) for op, ch in OP_CHAR_MAP.items()}

# The 3x3 trit truth table for the Crazy operation:
# crazy_trit[y][x]
_CRAZY_TRITS = (
    (1, 0, 0),
    (1, 0, 2),
    (2, 2, 1),
)


def crazy_op(x: int, y: int) -> int:
    """Canonical 10-trit crazy operation."""
    res = 0
    p = 1
    for _ in range(10):
        res += _CRAZY_TRITS[y % 3][x % 3] * p
        x //= 3
        y //= 3
        p *= 3
    return res


def rot_op(x: int) -> int:
    """Canonical 10-trit ternary rotation right (ROR)."""
    return (x // 3) + (x % 3) * 19683


def char_for_op(op: int, c: int) -> str:
    """Returns the unique ASCII character in [33, 126] that decodes to `op` at address `c`.
    
    Formula:
      idx = XLAT1.index(op_char)
      source_char = ((idx - c) % 94) + 33
    """
    if op not in OP_XLAT1_INDEX:
        raise ValueError(f"Unknown opcode: {op}")
    idx = OP_XLAT1_INDEX[op]
    ascii_val = ((idx - c) % 94) + 33
    return chr(ascii_val)


def op_for_char(char: str, c: int) -> int:
    """Returns the normalized opcode produced by `char` at address `c`."""
    ascii_val = ord(char)
    if not (33 <= ascii_val <= 126):
        raise ValueError(f"Character {char!r} out of printable ASCII range [33, 126]")
    idx = (ascii_val - 33 + c) % 94
    dec_ch = XLAT1[idx]
    return CHAR_OP_MAP.get(dec_ch, OP_NOP)


def xlat2_encrypt(char: str) -> str:
    """Encrypts a single ASCII character in [33, 126] through XLAT2."""
    val = ord(char)
    if not (33 <= val <= 126):
        return char
    return XLAT2[val - 33]
