# BolgeForge

**Sintetizador de quines Malbolge clásicas** — descárgalo, ejecútalo y produce
programas Malbolge que imprimen su propio código fuente byte a byte.

Récord del ecosistema: **quine clásica de 53,562 bytes (m=281)**, verificada con
doble motor C independiente (2026-10-17) — **6,290 B menor** que la quine de
referencia de Matthias Lutter (59,852 B) y 572 B menor que el récord anterior
(m=284, 54,134 B). Publicado en
[MALBOLGE-MB-DATABASE](https://github.com/DannyBaanks/Malbolge-MB-Database)
(artefacto + evidencia JSON).

## Quickstart

```bash
git clone https://github.com/DannyBaanks/BolgeForge.git
cd BolgeForge
make                    # opcional: compila el oráculo de verificación (gcc)

# Sintetizar el récord (~13 min, Python puro):
python3 synthesize.py 281
```

Salida esperada (final):

```
TOTAL FILE BYTES (wrapped at 72 chars/line): 53562 bytes!
WROTE EXACT QUINE FILE TO: .../artifacts/candidate_m281_53562b.mal
RUNNING CANONICAL OLMSTEAD VERIFICATION WITH .../mb_ref...
VERIFICATION PASS: EXACT 0-BYTE DIFFERENCE BIT-FOR-BIT!
CANONICAL MALBOLGE QUINE FOR m = 281 CONFIRMED!
```

La síntesis es **determinista**: `python3 synthesize.py 281` reproduce
exactamente el artefacto commiteado (`sha256 96b670b8…`). Sin compilador, el
sintetizador igualmente escribe el archivo — la verificación puede hacerse con
cualquier intérprete Malbolge Classic: la quine debe imprimir su propia fuente
sin una sola diferencia.

### Requisitos

- Python 3.8+ (solo stdlib)
- gcc o clang (opcional; solo para compilar el oráculo `mb_ref`)

### Valores de m conocidos

`m ≡ 2 (mod 3)` en [161, 314] es válido para el prefijo; que la quine **quepa**
depende del layout (stream cuasi-aleatorio de 24k–27k opcodes vs capacidad
`94m−467`):

| m | Bytes | Estado |
|---|---|---|
| **281** | **53,562** | **récord** (verificado 2 motores) |
| 284 | 54,134 | récord anterior (verificado 2 motores) |
| 287 | 54,706 | escalera (verificada) |
| 293 | 55,850 | escalera (verificada) |
| 308 | 58,709 | escalera (verificada) |

Otros `m` pueden terminar en `OVERFLOW`/`SYNTHFAIL` (diagnóstico propio del
sintetizador); es comportamiento esperado y documentado en `docs/NOTES.md`.

## Cómo funciona

Arquitectura de la línea Lutter, medida y reconstruida por síntesis:

1. **Objetivos**: se ejecuta la quine de Lutter 27,190 pasos y se registran los
   215 bytes que la máquina auto-modifica en esa región (los "variables").
2. **Grafo de 26 macros**: cada macro es una secuencia de auto-modificación
   verificada *pura* (mismo efecto para todo registro `a` de entrada), encadenada
   por Dijkstra sobre valores de la celda 154 para colocar el dato exacto en la
   celda objetivo.
3. **Incremento `DEST+9`**: al final de cada grupo de 9 celdas, la celda 148 debe
   avanzar +9. Búsqueda en runtime: macros duras → BFS acotado (≤24) →
   **fallback composite constructivo** (2 escrituras `V → W → V+9` garantizadas
   para valores muertos de acarreo; usado 1 vez en el récord, 68 ops).
4. **Capacidad**: el preámbulo debe quedar bajo `94m − 3`; el stream sintetizado
   que cabe es cuasi-aleatorio según el layout, por eso el récord descendió hasta
   m=281 pero no m=278.

Bitácora completa del desarrollo: [`docs/NOTES.md`](docs/NOTES.md).

## Verificación independiente

El oráculo `mb_ref` (C, Olmstead Classic) es una implementación independiente;
el registro publicado se verificó además con un segundo motor C
(`malbolge-original` de MALBOLGE-MB-DATABASE: 62,239,852 pasos | HALTED,
0 diferencias en los primeros 53,562 bytes; añade un `0x0A` final de convención
propia). Evidencia completa con hashes:
[`quine_53562_verification.json`](https://github.com/DannyBaanks/Malbolge-MB-Database/blob/master/quine/evidence/quine_53562_verification.json).

## Estructura

```
synthesize.py          ← el sintetizador (CLI)
constants.py           ← constantes de máquina Malbolge (tablas y ops de trits)
oracle/mb_ref.c        ← oráculo de verificación (compilar con `make`)
reference/             ← quine de referencia de Lutter (dato de entrada)
artifacts/             ← quines verificadas commiteadas (récord + escalera)
docs/NOTES.md          ← bitácora de investigación
```

## Procedencia

- Sintetizador: `synthesize.py` — port portable **v3.1**
  (sha256 `e401dec1…`) de `synthesize_v2.py` **v3** (sha256 `56088d2c…`), la
  versión que construyó el récord m=281. El port solo cambia paths y CLI;
  la regresión es byte-exacta (m=281 → `96b670b8…`, m=284 → `1808fd4d…`).
- Desarrollo activo en el monorepo ISyCo
  (`workspace/assembly/malbolge/bolge_forge/`); este repositorio es el hogar
  público y reproducible de la herramienta.
- Registro canónico de artefactos publicados:
  [MALBOLGE-MB-DATABASE](https://github.com/DannyBaanks/Malbolge-MB-Database).

## Límites (anti-fake)

- El claim de récord es **acotado**: menor que la referencia Lutter y la escalera
  propia; no hay barrido externo exhaustivo de todas las quines clásicas
  publicadas.
- Descenso por debajo de m=281: `NOT_DEMONSTRATED` (m=278 bloqueado por el piso
  del stream sintetizado; ver `docs/NOTES.md` §Next steps).
- Sub-20KB es imposible con esta arquitectura (requiere rediseño del write path).

## Licencia

MIT — ver [LICENSE](LICENSE). La quine de referencia de Lutter
(`reference/quine_lutter.malbolge`) se incluye con atribución como dato de
entrada; su crédito es de su autor.
