# Truth Machine independiente — Fase M1 (emisor infinito de '1') — 2026-10-24

`STATUS`: busqueda de prefijos puros **REFUTADA exhaustivamente hasta profundidad 6**
(295,584 programas, 0 sobrevivientes). M1 via este camino: `NOT_DEMONSTRATED`.
Objetivo del roadmap (item 22): sintesis independiente from-scratch de una Truth
Machine Classic — las existentes en BolgeForge son reproduccion (90 B, CC BY-SA 4.0)
y derivada por re-encoding.

## Motor y validacion

`kernel_search.py` implementa la semantica exacta (misma que
`tools/prove_truth_machine.py`, validada contra `oracle/mb_ref`):

- ops decodificadas `j i * p < / v o`; `<` emite `a & 255`; `/` pone `a = input`
  (59048 en EOF); `i` hace `c = mem[d]` y **la cifra post-ejecucion cae sobre la
  celda destino** (orden de `mb_ref.c:103/119/123`), luego `c += 1`, `d += 1`.
- llenado clasico de memoria: `mem[i] = crz(mem[i-1], mem[i-2])` (`mb_ref.c:89`).
- deteccion de ciclo: clave `(a,c,d)` + hash de estado completo, **store-first**
  (solo la primera ocurrencia por clave — igual que el prover).

Validacion contra el artefacto de referencia (`artifacts/truth_machine_classic_90b.mal`,
sha `1e34e2af...`): input `0` → `HALT` en paso 38, salida `30`; input `1` → `CYCLE`
en paso 1408, `cycle_start` 1000, periodo **408**, 58 salidas todas `0x31`.
Idéntico al prover y a lo documentado en `2026-10-22-truth-machine-variant/`.

Dos bugs del motor detectados y corregidos durante la validacion (quedan anotados
como metodologia, no como evidencia): (1) `/` faltaba y quedaba como NOP silencioso;
(2) la deteccion de ciclo sobrescribia el ancla por clave, deslizandola y perdiendo
el cierre de periodo 408 — el prover store-first lo detecta, el buggy no.

## Restricciones estructurales descubiertas

- Desde arranque frio `a=0`: `crz(0,y)` produce trits 0/1 solamente — **49
  (trits 1,1,2,1) es inalcanzable con un solo `p`**; requiere `*` sobre una celda
  con valor `rot^-1(49) = 147`, que no puede ser celda de programa (bytes 33..126)
  sino solo celda cola (lleno determinista) o instalada en runtime.
- El ciclo 408 de la referencia tiene una orbita de registros `(a,c,d)` de solo
  ~6 estados mientras la memoria cierra a 408 — el ancla de deteccion debe ser
  store-first para verlo.

## Busqueda exhaustiva (motor corregido, 3,000 pasos, todas las salidas deben ser 49)

| Profundidad | Programas | WRONG_OUT | HALT | INVALID_ENC | NONPRINTABLE | ESCAPE | Sobrevivientes |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 64 | 11 | 11 | 28 | 14 | 0 | **0** |
| 3 | 512 | 98 | 98 | 188 | 112 | 16 | **0** |
| 4 | 4,096 | 833 | 833 | 1,954 | 371 | 105 | **0** |
| 5 | 32,768 | 6,776 | 6,778 | 12,737 | 4,933 | 1,544 | **0** |
| 6 | 262,144 | 55,616 | 55,609 | 127,120 | 14,469 | 9,330 | **0** |
| 7 | 2,097,152 | 443,359 | 443,632 | 839,473 | 260,996 | 109,692 | **0** |
| 8 | 16,777,216 | 3,603,177 | 3,604,534 | 8,131,157 | 788,286 | 650,062 | **0** |

Total: **19,173,952 programas, 0 sobrevivientes** (profundidades 2-8 exhaustivas).

## Mecanismo de la referencia descifrado (analisis de nuestra propia reproduccion)

Traza entrada (input '1', pasos 0-37): `j` deref posiciona `d` en una ventana de
datos (41-62); `p` escribe valores crz en esa ventana (2 rondas con reset `j`);
`/` lee el input; `<` lo emite; el valor del input propaga por `p` hasta una celda
de salto (`mem[61]`) y el `i` en 37 ramifica: `c=73` (continuar) vs camino halt.
Traza de ciclo completa: `cycle_trace_1000_1408.txt`.

**El ciclo estable de 408 pasos NO contiene escrituras**: unidad de 6 pasos
`64:i 65:E 64:i 65:j 88:i 89:X` con X ciclando `t,<,2,Y` — la celda 89 orbita bajo
XLAT2 y decodifica `<` cada 4 visitas; `a` queda intacto (=49 desde el `/`). El
coreografo es el **d-flujo**: celdas nunca ejecutadas (no se cifran) cuyos valores
son direcciones de salto (33..126 = bytes de programa), consumidas por el `d` que
avanza +1 por paso, con resets `j`.

## Consecuencia para el diseno propio

La via sin instalador queda refutada hasta profundidad 8; el diseno propio debe
reproducir la clase de mecanismo con valores/estructura propios: (a) nucleo de
coreografia (d-flujo de direcciones + celda de salida con orbita XLAT2 alineada +
reset `j`), buscable con el motor validado; (b) entrada `/` + `<` + rama `p`
(crz(48/49, B) hacia `v` vs continuar). PENDIENTE (no iniciado).

## Veredicto

- **Prefijos puros (sin datos instalados en runtime) hasta 6 ops: REFUTADO** como
  camino a M1. Ningun programa de ≤6 ops decodificadas sobrevive 3,000 pasos.
- M1 (y por extension M2/M3 sobre esta via): `NOT_DEMONSTRATED`.
- Siguiente via planificada (no iniciada): construccion con **instalador** —
  arranque congelado + maquinaria de instalacion tipo ventana (la de
  `tools/resynthesize.py`) que coloque los datos del kernel (p.ej. celdas con
  `rot^-1(49)=147`, objetivos de salto) y un kernel de bucle autoreparable de
  patron propio; verificacion con prover + `mb_ref` + espejos independientes.

## Provenance

- Re-verificado hoy en `MALPAD/evidence/m2_state/truth_machine.mal` (254 B, hermano,
  2026-09-01): input `0` → rc 0, salida `30`; input `1` → rc 2 (MAX_STEPS), 478 B
  todas `0x31`. Precedente de arquitectura, no artefacto de BolgeForge.
- Agente bridge `opencode_malbolge_genealogy_1792832024`, topic `bolgeforge/truth-machine`.

## ERRATA 2026-10-25 (append-only; no reescribe lo anterior)

- La via "instalador" anunciada como PENDIENTE se ejecuto y **cerro** el 2026-10-25:
  `docs/evidence/2026-10-25-truth-machine-v5/` (120 celdas, loader estricto ACCEPT,
  `0` HALT / `1` ciclo 408). Este informe se conserva como evidencia negativa de
  la ruta de prefijos y del candidato v4.
- El candidato v4 de esta carpeta (`candidate_source.txt`, `candidate_bytes.txt`,
  `candidate_params.json`, `solver.py`) queda **REFUTADO** por loader estricto
  (35 celdas invalidas, `cell 47 decodes to '{'`), aunque funcionase en el motor
  exacto. Se commitea por primera vez hoy como evidencia negativa.
- Correccion de mecanica: la cifra post-instruccion cae sobre la celda de
  instruccion `mem[c]` (o sobre el destino en `i`), **no** sobre `mem[d]`; por eso
  los valores de ventana instalados (63 en 116/49/51) son estables y no se
  corrompen al ser leidos por `i`. La traza `cycle_trace_clean.txt` ya lo mostraba.
- Obstruccion demostrada por enumeracion: las posiciones loader-validas de un
  valor nunca difieren en 2 ni en 4 (indices de ops validas en XLAT1
  `{6,7,29,35,48,65,66,84}`), y la ventana exige R1 en `dG` y `dG+2` (o `dG-4`):
  instalar en runtime es obligatorio para esta familia de kernels.
