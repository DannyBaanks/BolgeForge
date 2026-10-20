# BolgeForge Roadmap: Más Allá de la Quine

De sintetizador del récord mundial de quines a la **suite canónica de reproducción, optimización y síntesis de programas en Malbolge Clásico**.

---

## 1. Estado Actual: Hitos Completados 🏆

- [x] **Récord Mundial de Quine Clásica (m=281, 53,562 bytes)**:
  - Reducción de **−6,290 bytes** respecto a la referencia de Matthias Lutter (59,852 B) y **−572 bytes** respecto al récord anterior (m=284).
  - Determinismo absoluto: síntesis reproducible bit a bit (`sha256 96b670b8...`).
  - Verificación dual en oráculos independientes de C (Olmstead semantics).
- [x] **Técnica Algorítmica `do_composite_inc`**:
  - Salto constructivo en dos escrituras `V -> W -> V+9` para valores muertos de acarreo en celda 148, eliminando bloqueos en la escalera de descenso.
- [x] **Integración del Corpus Canónico de `malbolge.org`**:
  - Incorporación en `reference/malbolge_org/` de `cat.mal` (9.5 KB), `digital_root.mal` (32.6 KB), `adder.mal` (57.3 KB) y quines 2012/2015.
  - Harness de pruebas automatizado (`test_corpus.py` / `make test-corpus`) integrado al CI.
- [x] **Truth Machine Canónica (105 bytes, `artifacts/truth_machine.mal`)**:
  - Primer Truth Machine formalmente demostrado en Classic Malbolge: parada en '0', streaming infinito en '1' con cero degradación de memoria.
- [x] **FizzBuzz Autónomo y de Sistema Cerrado (Zero-Stdin) (4,455 opcodes, 4,517 B, `artifacts/fizzbuzz.mal`)**:
  - Resolución del reto histórico de un FizzBuzz 100% puro y autónomo en Classic Malbolge: 100 líneas (413 B) emitidas bit a bit idénticas sobre `mb_ref` en 2 ms.
  - Cero dependencias de stdin (a diferencia del antecedente de `angel_p_57` de 2023 que ejecutaba 109 lecturas de entrada esperando EOF en el acumulador).
  - Arquitectura de cinta transportadora no colisionante con separación estricta de 2,055 celdas entre código ($c \ge 3315$) y datos ($d \le 1259$), y preámbulo algebraico de salto loco $\text{crazy}(\text{rot}^2(80), 72) = 3312$.
- [x] **Compresión del Corpus Canónico ($-19,270$ chars, $-15.98\%$)**:
  - Re-síntesis de preámbulos HeLL para los 4 grandes programas de Lutter/Iizawa en `artifacts/*_compressed.mal`.

---

## 2. Fase 1: Desensamble y Reproducción de `malbolge.org` 🔍

Los programas de `malbolge.org` fueron construidos con el ensamblador HeLL / framework LMAO de Lutter y presentan preámbulos sobredimensionados (~1.4 KB iniciales compartidos más secuencias de escritura tmp no minimizadas).

### Metas de Reproducción y Optimización:

1. **Micro-Cat (`cat.mal` optimizado)**
   - *Lutter original*: 9,503 bytes.
   - *Objetivo BolgeForge*: Sintetizar un cat interactivo directo < 1,000 bytes (o micro-cat sub-250B) eliminando el preámbulo macro innecesario para un bucle de I/O directo.
2. **Digital Root Re-sintetizado (`digital_root.mal`)**
   - *Lutter original*: 32,596 bytes.
   - *Objetivo BolgeForge*: Reconstruir el autómata de estados de reducción ternaria/decimal usando nuestro grafo de macros `EDGES` y Dijkstra. Meta estimada: **< 20,000 bytes** (~40% de reducción).
3. **Adder Re-sintetizado (`adder.mal`)**
   - *Lutter original*: 57,283 bytes.
   - *Objetivo BolgeForge*: Reensamblar el sumador arbitrario de dos operandos con tablas de acarreo compactas. Meta estimada: **< 35,000 bytes**.

---

## 3. Fase 2: El Santo Grial de Esolangs — Nuevos Programas Canónicos 🚀

Malbolge ha tenido históricamente menos de una docena de programas reales demostrados en 28 años de historia (1998–2026). BolgeForge cuenta con la infraestructura para diseñar y sintetizar programas inéditos:

1. **FizzBuzz Autónomo y de Sistema Cerrado (Zero-Stdin)** `[COMPLETADO]`
   - *Antecedente*: En septiembre de 2023, angel_p_57 generó un FizzBuzz de texto fijo (3,590 B) que depende de 109 lecturas de stdin (`/`) esperando EOF ($59,048$) en el acumulador como oráculo de constantes, bloqueándose en terminal interactiva.
   - *Solución BolgeForge*: La primera implementación 100% autónoma y de sistema cerrado (0 llamadas a stdin), inmune a terminales, con arquitectura de cinta transportadora lineal no colisionante, preámbulo de salto cuántico en $c=3315$, y 15 recetas unívocas para todos los caracteres necesarios (4,455 opcodes). 100% verificado en `mb_ref` con código de salida 0 y 413 bytes emitidos en 2 ms ([`artifacts/fizzbuzz.mal`](../artifacts/fizzbuzz.mal)).
2. **Fibonacci Generator**
   - Generación interactiva de la serie de Fibonacci en base 10 con suma de dígitos y emisión limpia.
3. **Rot13 / Cifrador de Texto**
   - Transformación de caracteres alfabéticos conservando saltos de línea y símbolos.
4. **Quine Paramétrica Arbitraria**
   - Extender `synthesize.py` para permitir la síntesis directa de cualquier `m` factible en la escalera, autoseleccionando fallbacks composite.

---

## 4. Fase 3: Tooling y Pipeline de Compilación 🛠️

- **HeLL Frontend / Compiler**:
  - Compilador de especificaciones de alto nivel (`.hell`) a código de máquina Malbolge con posicionamiento automático de bloques y enrutamiento por Dijkstra.
- **Decompilador / Trace Analyzer**:
  - Herramienta para inspeccionar programas `.mal` existentes, aislando bucles de ejecución de código auto-modificable y tablas de datos.
