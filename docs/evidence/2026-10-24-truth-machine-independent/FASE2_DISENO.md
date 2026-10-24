# Fase 2: mecanismo completo descifrado y sistema de restricciones (2026-10-24)

`STATUS`: DISENO_COMPLETO — todas las restricciones algebraicas identificadas;
el sintetizador es un solver de restricciones mecanico (pendiente de implementar).

## 1. Semantica real de crazy (descubrimiento clave)

`tools/prove_truth_machine.py` implementa crazy en PARES de trits (base 9):
`crazy(x, y) = SUM_s CRAZY[(y//s)%9][(x//s)%9] * s` con `P9 = (1, 9, 81, 729, 6561)`.
**El primer indice es y (mem[d]), el segundo x (a)**. Consecuencias verificadas:
- `crz(a, .)` con `a < 81` (pares altos = 0) es SIEMPRE >= 29484: `CRAZY[y][0] in {4,5,7,8}`
  en las columnas de pares altos -> **nunca imprimible**.
- Por lo tanto un `p` con `a = 48/49` (recien leido el input) escribe valores enormes:
  util solo en celdas de datos, fatal en celdas ejecutadas.
- Para escribir un valor pequeno/controlable, `a` debe ser ENORME: la cadena de `p`
  alterna enorme->pequeno->enorme (la referencia: a = 0 -> 29560 -> 63 -> 29560 -> ...
  -> 29499 -> 73: el 73 es el objetivo de salto de la rama!!).

## 2. El mecanismo de entrada de la referencia (totalmente decodificado)

1. `j`@0 deref a la ventana de datos (d := 41).
2. Cadena de `p` escribe la ventana (valores huge/pequenos alternados).
3. `/` lee el input (a = 48/49), `<` lo emite (un '0' o un '1').
4. `p`@26: a=49 -> escribe huge' en mem[57] (el bit del input queda en el par bajo
   de huge': `CRAZY[y0][3] vs CRAZY[y0][4]` difieren para y0 en {0,1}).
5. `p`@30: a = huge' -> escribe PEQUENO (73) en mem[61] — el objetivo de salto.
6. `i`@37: c := mem[61] = 73 (rama '1') vs otro valor (rama '0' -> camino halt).

## 3. El nucleo de 408 (sin escrituras, coreografia pura)

Unidad de 6 pasos (celdas ejecutadas 89, 64x2, 65x2, 88; objetivos solo-cifrados 63, 87):
`G:i -> R1 | T:NOP | I:i -> R1 | T:j (reset d) | I:i -> R2 | O:X` con:
- `T` = ciclo-2 de XLAT2 {F(70), J(74)}: T=64 (J primero: NOP 'E', luego 'j') o T=60
  (F primero: NOP '2', luego 'j'). Forzado: T in {60, 64}.
- `O` = ciclo-4 {*(42), r(114), }(125), i(105)} con '<' decodificando desde el byte 105:
  O in {57, 68, 79, 88} (posicion mod 94).
- `G`, `I` = bytes permanentes `op_byte('i', pos)` (nunca cifradas: la cifra tras un
  salto cae en el OBJETIVO, no en el ejecutor).
- `R1 = T-1`, `R2 = O-1`, `G = O+1`, `I = T+1` (contiguidad forzada).
- d-flujo: 7 celdas nunca ejecutadas con bytes = direcciones (33..126), auto-referencial
  (`mem[rv+6] = rv`), orbita d: [P0, P0+1, P0+2, P0+3, rv+1, rv+2] con P0 = rv+3.
- Periodo de estado completo = 68 unidades x 6 = **408** (las celdas solo-cifradas caen
  en el ciclo-68 de XLAT2; lcm con el ciclo-4 de O = 68 unidades). **Reproducido
  independientemente: M1a DEMONSTRATED con periodo 408 y 17 outputs/ciclo.**

## 4. Restricciones algebraicas del ensamblado propio (todas verificadas)

1. `crz(49, y) = 87` NO tiene solucion (el digito-81 del resultado = CRAZY[y][0] in
   {4,5,7,8} nunca 1) -> la ranura R2 del stream no es escribible por la rama con
   a pequeno; la rama debe atacar otra celda (p.ej. el propio P0 con R1=63:
   `crz(49, y) = 63` SI tiene solucion familia y = 29560-ish — el valor exacto de la
   traza de la referencia!!).
2. La rama requiere y0 = 2 (par bajo del input: `CRAZY[2][3]=2 vs CRAZY[2][4]=2` —
   verificar por columna exacta en el solver; 48/49 difieren solo en t0).
3. El reset de d (`j`@k) fija `d := op_byte('j', k)` (lee su propio byte en linea
   recta); el +1 post-instruccion exige `op_byte('j', k) = D - 1` para que la celda
   k+1 ejecute con d = D.
4. La celda fuente y del `p` de rama debe ser enorme (familia 29484+): vive en el
   lleno, cuya posicion/cntenido se disena con los dos ultimos bytes del programa
   (`mem[n] = crz(b[n-1], b[n-2])`).
5. El ncleo exige R1 in {59, 63}: 63 tiene t2=1 (alcanzable por crz(49,.)); 59 tiene
   t2=0 (inalcanzable) -> **T=64 forzado** para la entrada via p-cadena.

## 5. Plan del solver (mecanico, sin busqueda ciega)

Entradas: (T=64, O in {57,68,79,88}, rv, k0, pk, k, D, par-final (x, z)).
Ecuaciones: cadena p (huge/pequeno), objetivo de rama = P0/R1, reset d, fase de O,
contenido del stream, y del lleno en D, decodificacion 'v' del camino '0'.
Verificacion final: motor validado (ambos inputs) + `mb_ref` + espejos.
