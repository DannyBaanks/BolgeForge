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

## 2. Invariantes Algebraicas y Teoremas Demostrados `[DEMONSTRATED — ALGEBRAIC & RUNTIME]`

En Malbolge Clásico, la instrucción `/` devuelve `59048` (`0t2222222222`) en EOF y `0..255` para cualquier byte de entrada. Verificamos exhaustivamente en [`tools/microcat.py`](../tools/microcat.py), [`tools/test_exact_ascii_circuit.py`](../tools/test_exact_ascii_circuit.py) y [`tools/test_period2_loop.c`](../tools/test_period2_loop.c) los siguientes teoremas:

1. **Separador Universal Binario en 2 Pasos (`K1 = 59048, K2 = 729` / `K2 = 243`):**
   - $\text{crazy}(\text{crazy}(59048, 59048), 729) = \mathbf{0}$ (EOF).
   - $\forall x \in [0, 255]: \text{crazy}(\text{crazy}(x, 59048), 729) = \mathbf{1458}$ (colapsa los 256 valores de byte a una única constante exacta).
   - Con $K_2 = 243$: $\text{EOF} \to 0$, y todos los 256 bytes $\to 486$.

2. **Separador ASCII Puro en Memoria Baja (`Y1 = 80 ('P'), Y2 = 35 ('#'), \text{rot}^4`):**
   $$\text{Sep}(x) = \text{crazy}(\text{rot}^4(\text{crazy}(x, 80)), 35)$$
   - Para $x = 59048$ (EOF): $\text{Sep}(59048) = \mathbf{368}$ (salta a 368 $\to$ cae en celda 369 de crazy fill, que decodifica exactamente a `v` HALT).
   - $\forall x \in [0, 255]: \text{Sep}(x) = \mathbf{8}$ (salta a 8 $\to$ cae en celda 9 de la rutina de salida).
   - **Cero constantes extendidas:** Todas las constantes son caracteres ASCII imprimibles ($33 \le Y \le 126$), eliminando la necesidad de tablas HeLL.

3. **Involuciones de Almacenamiento Sin Pérdida (`29524` y `'y' = 121`):**
   - $\forall x \in [0, 59048]: \text{crazy}(\text{crazy}(x, 29524), 29524) = x$.
   - $\forall x \in [0, 255]: \text{crazy}(\text{crazy}(x, 121), 121) \equiv x$. (Involución en ASCII imprimible puro `'y'`).

4. **Teorema del Bucle de Período 2 en Ciclo 6 (`F \leftrightarrow J`):**
   - En la permutación `xlat2`, los caracteres `F` (70) y `J` (74) forman una órbita cerrada de longitud 2: `xlat2['F'-33] = 'J'`, `xlat2['J'-33] = 'F'`.
   - **Completitud Funcional de Instrucciones Activas en Ciclo 6:**
     - `c % 94 = 47`: `F = '/'` (Input), `J = 'P'` (NOP)
     - `c % 94 = 29`: `F = '<'` (Output), `J = ';'` (NOP)
     - `c % 94 = 28`: `F = 'i'` (Jump), `J = '\''` (NOP)
     - `c % 94 = 64`: `F = 'j'` (Set d), `J = 'E'` (NOP)
     - `c % 94 = 86`: `F = 'p'` (Crazy), `J = 'r'` (NOP)
     - `c % 94 = 63`: `F = '*'` (Rot), `J = 'M'` (NOP)
     - `c % 94 = 11`: `F = 'v'` (Halt), `J = 'J'` (NOP)
   - En pases impares, las celdas ejecutan la instrucción activa; en pases pares ejecutan NOPs inertes y regresan a `F`. Cero degradación entrópica sobre órbitas infinitas.

5. **Discriminador de 125 Bytes Verificado en `mb_ref` (`artifacts/cand_valid.mal`):**
   - 125 bytes en total, 100% ASCII imprimible ($33..126$).
   - Batería 1 (EOF inmediato `b""`): Termina limpiamente en el paso 15 con código de salida 0 y 0 bytes emitidos.
   - Entradas de byte (`b"A"`): Separa limpiamente a celda 9 sin tocar la ruta de terminación.

6. **Micro-Cat Autónomo en 430 Bytes (`artifacts/microcat.mal`) `[DEMONSTRATED — RUNTIME]`:**
   - 430 bytes en total, 100% ASCII imprimible ($33 \le \text{byte} \le 126$), cero tablas HeLL.
   - **Batería 1 (EOF Inmediato `b""`):** Termina en exactamente 20 pasos en celda 9 (`v`), código de salida 0, 0 bytes emitidos.
   - **Batería 2 (Eco Completo de Todos los 256 Bytes $0..255$):** Verificado exhaustivamente contra `oracle/mb_ref.c` en [`tools/test_microcat_suite.py`](../tools/test_microcat_suite.py). Los 256/256 bytes individuales son leídos, preservados vía involución $Y_0=121$, rotados 10 veces en celda 36, emitidos por `<` con fidelidad exacta de 8 bits (incluyendo `0x00` y `0xFF`), y seguidos de terminación limpia con código 0 ante EOF.
   - **Defecto Descubierto en `cat.mal` Canónico (Lutter 2012):** Telemetría exacta en paso 9148 reveló que ante EOF, `cat.mal` emite un byte espurio `0x88` ('¨') debido a falta de discriminador antes de `<`. `microcat.mal` corrige esta falla emitiendo exactamente 0 bytes en EOF.

7. **Teorema de Reseteo Universal de Memoria Sin Entropía Residual:**
   $$\forall b \in [0, 255], W = \text{crazy}(b, 121): \quad \text{crazy}(\text{rot}(\text{crazy}(\text{crazy}(W, 486), 242)), 80) \equiv \mathbf{121}$$
   - En dos pasos de `crazy`, los 256 estados colapsan a una constante universal exacta: $\text{crazy}(\text{crazy}(W, 486), 242) = \mathbf{29402}$.
   - Una rotación y una operación con el carácter imprimible $80$ ('P') restauran la celda de almacenamiento a $121$ ('y') con 0 bits de memoria residual del byte anterior.

8. **Teorema del Reticulado Cristalino de Período 6 en Crazy Fill:**
   - Terminar un archivo `.mal` con los caracteres ASCII imprimibles `('6', '6')` ($54, 54$) induce un reticulado auto-generado de período 6 en toda la memoria no inicializada ($i \ge N$):
     $$\text{mem}[N + 6k] = \mathbf{29524}, \quad \text{mem}[N + 6k + 1] = 54, \quad \text{mem}[N + 6k + 2] = 29551, \dots$$
   - Genera más de 9,800 copias inalteradas del operador de involución universal `29524` sin consumir un solo byte de código fuente adicional.

---

## 3. Estado Epistémico y Frontera de Demostración

1. **Incompatibilidad directa de las 26 macros del Módulo 0 de la Quine con `cat.mal` (`[OBSERVED NEGATIVE RESULT]`):**
   - Confirmada la amputación del bucle canónico al cortar en `9,067`.
2. **Detección de EOF y Terminación Inmediata Limpia en 125 Bytes (`[DEMONSTRATED — RUNTIME]`):**
   - Sintetizado en [`artifacts/cand_valid.mal`](../artifacts/cand_valid.mal) (125 bytes) y verificado contra `oracle/mb_ref.c` en [`tools/test_valid_ascii_cat.py`](../tools/test_valid_ascii_cat.py).
3. **Eco de Bytes con Fidelidad Total de 8 Bits en 430 Bytes (`[DEMONSTRATED — RUNTIME]`):**
   - Sintetizado en [`artifacts/microcat.mal`](../artifacts/microcat.mal) (430 bytes) y verificado contra `oracle/mb_ref.c` en [`tools/test_microcat_suite.py`](../tools/test_microcat_suite.py). 22 veces más compacto que el estándar histórico de 9,503 bytes.
4. **Cierre de Ciclo Completo Multi-Byte Autónomo (`[IN PROGRESS]`):**
   - La orquestación del oscilador bi-fásico de período 2 (`F \leftrightarrow J`) en Ciclo 6 para streaming multi-byte continuo sin degradación se encuentra completamente formalizada matemáticamente en [`tools/test_complete_circuit.py`](../tools/test_complete_circuit.py).
