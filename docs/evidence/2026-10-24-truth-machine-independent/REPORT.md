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

Salidas crudas: `depth{2..6}_out.txt`, `beam_out.txt`, `profile_seed9803.txt` (del
experimento hermano). Los archivos de profundidad 2-6 se regeneraron tras corregir
`/`; los numeros de WRONG_OUT/HALT cambian levemente vs la corrida pre-correccion
(los prefijos con `/` ahora mueren correctamente en su primer `<`).

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
