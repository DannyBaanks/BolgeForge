# Truth Machine Clásica independiente v5 — 120 celdas, loader estricto

Fecha: 2026-10-25. Artefacto: `tm_independent_v5.mal` (120 celdas).
SHA-256: `7b74ec811d9f44d609cee4a51323e2fdc4d73bda77a675ccbfa4ed9db0556961`.

## Resultado

| Rama | Comportamiento | Evidencia |
|---|---|---|
| entrada `0` | emite exactamente un `0` (0x30) y **HALT** en el paso 27 | prover `branch_zero`, `mb_ref` rc=0 stdout `30` |
| entrada `1` | **nunca** termina; **todas** las salidas son `1` (0x31) | prover: ciclo de estado completo, periodo 408, 17 salidas/ciclo, `state_sha256 c36f15dc…`; `mb_ref` 200k pasos → 8.334 bytes, 1M pasos → 41.667 bytes, conjunto de valores `{0x31}` |
| loader estricto | **ACCEPT**, 0 celdas inválidas | `tools/prove_truth_machine.py` (`loader: ACCEPT`), `oracle/mb_ref.c` recompilado |

Veredicto del prover: `DEMONSTRATED` (rc=0), las seis comprobaciones en `true`
(`prover_output.json`).

`o` no es instrucción en este dialecto (es no-op); `mb_ref` y el prover usan el
mismo dialecto, y ambos coinciden con este programa.

## Por qué es una síntesis independiente

Nada del artefacto de referencia (`artifacts/truth_machine_classic_90b.mal`,
90 celdas, CC BY-SA 4.0) se copia:

| Elemento | Referencia 90b | v5 (este artefacto) |
|---|---|---|
| Longitud | 90 | 120 |
| Kernel | `63/64/65` + `87/88/89` | `63/64/65` + `78/79/80` |
| Ventana | `47..52` | `112..117` |
| Instalación en runtime | `63` en `49` y `51` (a=0→29560→63) | `63` en `116` (a=0→29533→63) |
| Entrada / rama | propia de la referencia | 27 celdas propias, rama por `i` sobre `mem[42]` |
| Constantes de la rama | — | `ya=117@75`, `yb=39@42`, `y0=103@59`, `w=76@116` |

La mecánica del ciclo (j/NOP alternante, `i` que aterriza en R1/R2, ciclo de
cifrado de 4 en O) es el mecanismo ya descifrado en M1/Fase 2 y es común a
cualquier kernel de esta familia; lo sintetizado aquí es la geometría, la
entrada, la rama y el instalador.

## Derivación (reproducible con `build_v5.py`)

1. **Kernel propio.** Catálogo de la Fase 2: `T ∈ {60,64,88,92}` (ciclo-2 j/NOP),
   `O ∈ {57,68,79,88}` (ciclo-4 con un `<`). Se elige `T=64, I=65, R2=78, O=79,
   G=80` con ventana en `d1=112`: `mem[112]=63`, `mem[114]=78`, `mem[116]=63`,
   `mem[117]=111`.
2. **Obstrucción del loader (DEMOSTRADO por enumeración).** Las posiciones donde
   un valor es loader-válido nunca difieren en 2 ni en 4 (los índices de ops
   válidas en XLAT1 son `{6,7,29,35,48,65,66,84}`). La ventana del kernel exige
   `R1` en `dG` y en `dG+2` (o `dG-4`), así que **al menos una** celda de la
   ventana no puede ser loader-válida: hay que instalarla en runtime.
3. **Instalador.** Con `a=0` al arrancar, un `p` da un valor enorme:
   `crazy(0,103)=29533`. El segundo `p`, con `d=116`, calcula
   `crazy(29533, mem[116])`; el único byte loader-válido en 116 que produce `63`
   es `76`. Instalación: `mem[116]=63` en el paso 4.
4. **Rama.** `p@75` (`ya=117`) y `p@42` (`yb=39`) dan
   `B1 = crazy(crazy(49,117),39) = 49` y `B0 = crazy(crazy(48,117),39) = 48`.
   `i@26` con `d=42` lee `mem[42]`: con `49` salta a 49 y sigue a 50 (kernel);
   con `48` salta a 48, cifra `mem[48]` y ejecuta 49 = `v` (HALT).
   Invariante observada por enumeración completa: con esta cadena de dos `p`
   desde el par `(49,48)`, **siempre** `B1=49 ⇒ B0=48`.
5. **Gobierno.** `j@50` lee `mem[43]=113` y deja `d=114`; `i@51` lee
   `mem[114]=78` y aterriza en `O=79` con `d=115`, entrando al kernel con `a=49`
   (por eso la rama `1` emite `0x31`).

## Límites declarados

- **Pruebas finitas.** El prover demuestra la repetición de estado completo en
  el paso 1.408 con periodo 408; el oráculo C se ejecutó hasta 1.000.000 de
  pasos (41.667 salidas). No se ejecutó ninguna prueba infinita (imposible).
- **No comparado** con `truth_machine_classic_90b.mal` en tamaño ni velocidad:
  el objetivo era independencia y aceptación del loader, no optimalidad.
- El artefacto v4 (2026-10-24) queda como **evidencia negativa**: funcionaba en
  el motor exacto pero violaba el loader estricto en 35 celdas
  (`LOADER_REJECT: cell 47 decodes to '{'`); se conserva en
  `../2026-10-24-truth-machine-independent/` (sin commitear hasta hoy).
- La frase "independiente" se limita a lo enumerado arriba: comparte con la
  referencia el *mecanismo* del kernel, que ya era conocimiento público del
  proyecto desde la Fase 2.

## Reproducir

```bash
python3 docs/evidence/2026-10-25-truth-machine-v5/build_v5.py     # regenera el .mal
python3 tools/prove_truth_machine.py docs/evidence/2026-10-25-truth-machine-v5/tm_independent_v5.mal --json
cc -O2 -o /tmp/opencode/mb_ref oracle/mb_ref.c
echo -n 0 | /tmp/opencode/mb_ref docs/evidence/2026-10-25-truth-machine-v5/tm_independent_v5.mal 200000
echo -n 1 | /tmp/opencode/mb_ref docs/evidence/2026-10-25-truth-machine-v5/tm_independent_v5.mal 200000
```
