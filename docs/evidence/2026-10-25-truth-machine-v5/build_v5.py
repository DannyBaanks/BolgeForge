#!/usr/bin/env python3
"""Constructor reproducible de la Truth Machine Clasica independiente v5 (120 celdas).

Derivacion completa (2026-10-25). Todo el programa es sintetizado aqui: entrada,
rama, instalador y geometria del kernel son propios; no se copia ninguna celda
del artefacto de referencia de 90 bytes.

Dialecto del proyecto (identico a oracle/mb_ref.c y tools/prove_truth_machine.py):
  '<' -> putchar(a)      (SALIDA)
  '/' -> a = getchar()   (ENTRADA)
  'o' -> no-op           (la validacion del loader lo acepta)
  'j' 'i' 'p' '*' 'v'   (semantica Olmstead)

Loader estricto: toda celda p del cuerpo debe cumplir
  xlat1[(byte - 33 + p) % 94] in "ji*p</vo".

Geometria
---------
Kernel (propio, distinto de la referencia 63/64/65/87/88/89):
  63 = R1 (celda de aterrizaje)   64 = T (j/NOP alternante)
  65 = I                          78 = R2 (celda de aterrizaje)
  79 = O (ciclo t/< /2/Y, una salida por ciclo)   80 = G ('i' fijo)
Ventana en d1=112: mem[112]=63, mem[114]=78, mem[116]=63 (INSTALADO), mem[117]=111.

Unidad estable (6 instrucciones por vuelta de cifrado):
  O en d=115 -> G en d=116 lee mem[116]=63 -> T(64) en d=117 'j' lee mem[117]=111
  -> I(65) en d=112 lee 63 -> T(64) en d=113 NOP -> I(65) en d=114 lee 78
  -> O en d=115 -> G en d=116 ...

Entrada (0..10), instalador y rama:
  0  'j'  d := mem[0]=40 -> 41
  1  'j'  d := mem[41]=58 -> 59
  2  'p'  d=59  : a = crazy(0, mem[59]=103) = 29533      (a inicial 0)
  3  'j'  d := mem[60]=115 -> 116
  4  'p'  d=116 : a = crazy(29533, mem[116]=76) = 63      INSTALA 63 en 116
  5  '/'  a = entrada (49 o 48)
  6  '<'  emite la entrada  (0 -> un '0'; 1 -> primer '1')
  7  'j'  d := mem[119]=74 -> 75
  8  'p'  d=75  : a = crazy(entrada, mem[75]=117)
  9  'j'  d := mem[76]=41 -> 42
 10  'p'  d=42  : a = crazy(a, mem[42]=39) = B1 ; escribe mem[42]=B1
 11..24 NOP (d 43..56)
 25  'j'  d := mem[57]=41 -> 42
 26  'i'  c := mem[42] = B1        RAMA
     B1 = 49 (entrada '1') -> c=49, cifra mem[49], ejecuta 50
     B0 = 48 (entrada '0') -> c=48, cifra mem[48], ejecuta 49 = 'v' HALT
 49  'v'  parada de la rama 0
 50  'j'  d := mem[43]=113 -> 114
 51  'i'  c := mem[114]=78 -> O(79) en d=115 -> G en 116  (entrada al kernel)

Algebra (verificada por enumeracion en el informe):
  crazy(crazy(49,117),39) = 49   y   crazy(crazy(48,117),39) = 48
  crazy(0,103) = 29533 ; crazy(29533,76) = 63
  Instalar 63 en 116 exige w=76 (unico byte loader-valido en 116 que sirve).
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.prove_truth_machine import XLAT1, VALID, crazy  # noqa: E402

INV = {c: i for i, c in enumerate(XLAT1)}


def op_byte(op: str, cell: int) -> int:
    """Byte que decodifica `op` en la celda `cell`."""
    return (INV[op] - cell) % 94 + 33


def build() -> bytes:
    n = 120
    cells = [op_byte("o", i) for i in range(n)]  # relleno NOP loader-valido
    put = lambda i, v: cells.__setitem__(i, v)  # noqa: E731

    # entrada + instalador + rama
    for i, op in enumerate("jjpjp/<jpjp"):
        put(i, op_byte(op, i))
    put(25, op_byte("j", 25))
    put(26, op_byte("i", 26))
    put(41, 58)    # fuente del salto 1: 59 - 1
    put(42, 39)    # yb
    put(43, 113)   # fuente del salto de gobierno
    put(49, op_byte("v", 49))
    put(50, op_byte("j", 50))
    put(51, op_byte("i", 51))
    put(57, 41)    # fuente del salto 25 -> 42
    put(59, 103)   # y0 del instalador
    put(60, 115)   # salto al instalador: 116 - 1

    # kernel
    put(63, op_byte("o", 63))
    put(64, op_byte("j", 64))
    put(65, op_byte("i", 65))
    put(75, 117)   # ya
    put(76, 41)    # salto 9 -> 42
    put(78, op_byte("o", 78))
    put(79, op_byte("<", 79))
    put(80, op_byte("i", 80))

    # ventana (116 se instala en runtime)
    put(112, 63)
    put(114, 78)
    put(116, 76)
    put(117, 111)
    put(119, 74)   # salto 7 -> 75
    return bytes(cells)


def check(cells: bytes) -> None:
    bad = [
        (i, XLAT1[(v - 33 + i) % 94])
        for i, v in enumerate(cells)
        if XLAT1[(v - 33 + i) % 94] not in VALID
    ]
    assert not bad, f"celdas no loader-validas: {bad[:8]}"
    assert crazy(0, 103) == 29533
    assert crazy(29533, 76) == 63
    assert crazy(crazy(49, 117), 39) == 49
    assert crazy(crazy(48, 117), 39) == 48


def main() -> int:
    cells = build()
    check(cells)
    out = Path(__file__).with_name("tm_independent_v5.mal")
    out.write_bytes(cells)
    print(f"{out.name}: {len(cells)} celdas  sha256={hashlib.sha256(cells).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
