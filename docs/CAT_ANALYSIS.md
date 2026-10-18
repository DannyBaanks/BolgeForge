# Desensamble y Análisis Arquitectónico de Cat en Malbolge Clásico

Investigación y telemetría exacta del programa `cat.mal` (9,503 B) de [malbolge.org](https://malbolge.org/) desarrollado por Matthias Lutter (2012), invariantes algebraicas de detección de EOF en 2 pasos, y registro de límites experimentales (`[CURRENT]` vs `[NOT_DEMONSTRATED]`).

---

## 1. Telemetría Exacta de `cat.mal` (Lutter, 2012) `[CURRENT]`

Verificado dinámicamente con [`oracle/mb_ref.c`](../oracle/mb_ref.c) y [`tools/audit_bloat.py`](../tools/audit_bloat.py):

- **Tamaño total:** 9,503 bytes (**9,382** instrucciones ASCII sin espacios).
- **Fin del preámbulo lineal:** `c = 9,003` (**paso 8,905**, donde ocurre el primer salto `i` fuera del stream lineal después de `c = 0`). Representa el **96.0%** de los opcodes del archivo.
- **Primer I/O (`/`):** Ocurre en el **paso 8,992** en `c = 9,067, d = 58,999, a = 29,524`.
- **Celdas modificadas por `*` / `p` durante el preámbulo:** **161 celdas** en total:
  - **38 celdas en memoria baja** (`< 9,382`, específicamente en `33..96`).
  - **123 celdas en memoria alta** (`58,844..59,048`).
- **Celdas de código (`c`) ejecutadas post-I/O:** **36 celdas distintas**:
  - **22 celdas en memoria baja:** `c = 0` (portal de salto `i`) y trampolines en `9,025..9,371` (nota: la instrucción `v` HALT reside en `c = 9,025` y el trampolín `j, i` en `9,049..9,050`, **antes** de `first_io_c = 9,067`).
  - **14 celdas en memoria alta:** código en `58,845..58,927` más el puente de wraparound `59,047..59,048 -> 0`.

---

## 2. Invariante Algebraica: Detector de EOF Ternario en 2 Pasos `[DEMONSTRATED — ALGEBRAIC]`

En Malbolge Clásico, la instrucción `/` devuelve `59048` (`0t2222222222`) en EOF y `0..255` para cualquier byte de entrada. Verificamos exhaustivamente en [`tools/microcat.py`](../tools/microcat.py) las siguientes identidades de la operación `crazy`:

1. **Detector de EOF en 2 pasos (`K1 = 59048, K2 = 29524`):**
   $$\text{EOF\_CHECK}(x) = \text{crazy}(\text{crazy}(59048, x), 29524)$$
   - Para $x = 59048$ (EOF): $\text{crazy}(59048, 59048) = 29524 \implies \text{crazy}(29524, 29524) = \mathbf{0}$.
   - Para todo $x \in [0, 255]$: $\text{EOF\_CHECK}(x) > 0$ (**0 colisiones** en los 256 valores de byte).

2. **Separador Universal Binario (`K1 = 59048, K2 = 729`):**
   - $\text{crazy}(\text{crazy}(59048, 59048), 729) = \mathbf{0}$ (EOF).
   - $\forall x \in [0, 255]: \text{crazy}(\text{crazy}(x, 59048), 729) = \mathbf{1458}$ (colapsa los 256 valores de byte a una única constante exacta).

3. **Involución de Almacenamiento Sin Pérdida (`29524`):**
   - $\forall x \in [0, 59048]: \text{crazy}(\text{crazy}(x, 29524), 29524) = x$.

---

## 3. Resultados Negativos y Estado Epistémico `[NOT_DEMONSTRATED]`

1. **Incompatibilidad directa de las 26 macros del Módulo 0 de la Quine con `cat.mal` (`[OBSERVED NEGATIVE RESULT]`):**
   - Los scripts exploratorios [`tools/synthesize_cat.py`](../tools/synthesize_cat.py) y [`tools/generate_compact_cat.py`](../tools/generate_compact_cat.py) intentaron reemplazar el preámbulo de `cat.mal` usando el grafo de 26 macros puras de `synthesize.py` (`*jo`, `oojo*popjo`, etc.) y cortando el bucle en `c = 9,067`.
   - **Por qué falla (`candidate_cat_7893b.mal` imprime `H9\x12` ante `"Hello"`):**
     1. Las macros de `synthesize.py` contienen instrucciones `j` diseñadas para el bucle enrollado del Módulo 0 de la quine (celdas `33..154`), que **no existe** en el preámbulo lineal HeLL de `cat.mal`.
     2. Cortar el bucle en `first_io_c = 9,067` amputa las celdas `9,025` (`v` HALT) y `9,049..9,050` (`j, i`), que pertenecen al bucle principal.
     3. Rellenar con NOPs (`'o'`) desplaza el puntero `d` en `+1` por cada celda de relleno.
2. **Ensamblado de un `microcat.mal` autónomo sub-1KB (`[NOT_DEMONSTRATED]`):**
   - Aunque las invariantes algebraicas de detección de EOF y la involución `29524` están probadas matemáticamente, el cierre completo de la máquina de estados en código Malbolge auto-modificante aún no ha sido construido.
   - El archivo `artifacts/microcat.mal` verificado por [`tools/assemble_microcat.py`](../tools/assemble_microcat.py) es únicamente un re-empaquetado a 72 columnas del `cat.mal` canónico de Lutter (`9,382` opcodes) utilizado para validar el arnés de 4 baterías de `mb_ref`.
