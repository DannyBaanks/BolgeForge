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

1. **FizzBuzz en Malbolge Clásico**
   - *Estado en la comunidad*: Reto abierto mítico. Casi todas las versiones existentes dependen de Malbolge Unshackled (memoria infinita) o trampas de intérprete.
   - *Enfoque BolgeForge*: Bucle de conteo de 1 a 100 con comprobación periódica de divisibilidad por 3 y 5 en memoria estática de 59,049 celdas.
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
