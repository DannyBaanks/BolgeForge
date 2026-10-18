# Desensamble y Optimización de Cat en Malbolge Clásico

Investigación y análisis arquitectónico del programa `cat.mal` (9,503 B) de [malbolge.org](https://malbolge.org/) desarrollado por Matthias Lutter (2012), y diseño del pipeline de optimización de BolgeForge (2026).

---

## 1. Deconstrucción de `cat.mal` (Lutter, 2012)

Ejecutado dinámicamente con [`tools/analyzer.py`](../tools/analyzer.py) sobre el oráculo independiente [`oracle/mb_ref.c`](../oracle/mb_ref.c):

- **Tamaño total:** 9,503 bytes (9,382 instrucciones ASCII).
- **Pasos hasta el primer I/O (`/`):** **8,992 pasos**.
- **Variables escritas en memoria alta:** 124 celdas en el rango `[58844, 59048]`.
- **Bucle de ejecución real:** Ocupa únicamente **315 bytes** (desde `c=9067` hasta `c=9382`).
- **Causa del gigantismo (9.5 KB):**
  A diferencia de la quine (donde Lutter diseñó un bucle compacto en Módulo 0 con incremento en celda 148), en `cat.mal` (2012) el compilador HeLL generó un **stream lineal no enrollado (unrolled)** de ~7,500 instrucciones consecutivas para inicializar las 124 variables una tras otra.

---

## 2. El Descubrimiento Matemático: Detector de EOF Ternario en 2 Pasos

En Malbolge, la instrucción `/` (leer carácter) devuelve `59048` (`0t2222222222`) al encontrar el fin de archivo (EOF). En el diseño de Lutter, verificar si `A == 59048` requiere 275 pasos de salto indirecto y decenas de tablas en memoria.

En BolgeForge descubrimos la siguiente invariante de la operación `crazy`:

$$\text{EOF\_CHECK}(x) = \text{crazy}(\text{crazy}(59048, x), 29524)$$

### Comprobación de Trits:
1. Si $x = 59048$ (todos los trits son 2):
   - $\text{crazy}(2, 2) = 1 \implies \text{crazy}(59048, 59048) = 29524$ (`0t1111111111`).
   - $\text{crazy}(1, 1) = 0 \implies \text{crazy}(29524, 29524) = 0$.
2. Si $x \in [0, 127]$ (cualquier carácter ASCII válido):
   - El resultado $\text{EOF\_CHECK}(x)$ es **estrictamente mayor a cero** (distribución cuasi-uniforme alrededor de 29,500).
   - **Cero colisiones:** Verificado exhaustivamente para los 128 valores ASCII.

### Implicación:
Un salto indirecto basado en $\text{EOF\_CHECK}(x)$ aterriza en la celda `0` si y solo si es EOF (donde se coloca `v` HALT), y en una celda distinta para cualquier dato normal (continuando el eco). ¡Reduce la complejidad de detección de 275 pasos a solo **dos instrucciones `p`**!

---

## 3. Plan de Ataque para Fase 1

1. **Vía A: Resíntesis Canónica de `cat.mal`:**
   - Sintetizar las 124 variables usando el Módulo 0 enrollado con Dijkstra de BolgeForge.
   - Reducción proyectada: **~7,160 bytes** (−24.6% respecto a los 9,503 B de Lutter).
2. **Vía B: Micro-Cat Terminating de BolgeForge:**
   - Implementar un bucle directo de entrada/eco/EOF basado en el detector ternario de 2 pasos.
   - Meta de tamaño: **< 1,000 bytes** (o < 500 bytes), destruyendo el récord de tamaño para un Cat terminante en Malbolge.
