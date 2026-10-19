# BolgeForge

**Sintetizador y laboratorio de programas autónomos en Malbolge Clásico (Ben Olmstead, 1998)** — motor formal para generar quines récord, programas streaming y máquinas de estados libres de degradación entrópica sobre el toro de 59,049 celdas.

---

## 🏆 Hitos y Récords del Ecosistema

1. **Récord Mundial de Quine Clásica: 53,562 bytes ($m=281$)**
   - Verificada con doble motor C independiente (2026-10-17).
   - **6,290 B menor** que la quine histórica de Matthias Lutter (59,852 B, 2012) y 572 B menor que el récord anterior ($m=284$, 54,134 B).
   - Publicado en [MALBOLGE-MB-DATABASE](https://github.com/DannyBaanks/Malbolge-MB-Database) con evidencia JSON criptográfica (`sha256 96b670b8…`).

2. **MicroCat Autónomo Multi-Etapa: 3,380 bytes (`artifacts/microcat.mal`)**
   - **2.8 veces más compacto** que el estándar histórico de 9,503 bytes de Matthias Lutter (`reference/malbolge_org/cat.mal`).
   - **Corrección del Bug Histórico de EOF (2012):** En el paso 9,148 de `cat.mal` canónico, ante un flujo de entrada vacío (`b""`) o al terminar el archivo, la máquina emitía un byte espurio `0x88` ('¨') antes de detenerse. `microcat.mal` introduce un discriminador algebraico de 2 pasos previo a la instrucción de salida `<`, logrando terminación limpia con código 0 y exactamente **0 bytes emitidos**.
   - **100% de Fidelidad de 8 bits:** Verificado contra `oracle/mb_ref.c` en todas las baterías de prueba (entradas vacías, los 256 bytes individuales $0..255$, pares de bytes y cadenas multi-byte).

---

## Quickstart

```bash
git clone https://github.com/DannyBaanks/BolgeForge.git
cd BolgeForge
make                    # Compila el oráculo de referencia en C (oracle/mb_ref)
```

### 1. Ejecutar y Verificar MicroCat (3,380 B)

```bash
# Probar stdin vacío (debe emitir 0 bytes y retornar código 0):
./oracle/mb_ref artifacts/microcat.mal < /dev/null
echo "Exit code: $?"

# Probar eco de texto:
echo -n "ABC" | ./oracle/mb_ref artifacts/microcat.mal
echo ""

# Ejecutar la suite completa de baterías (256 bytes, pares y secuencias):
python3 tools/test_three_stage_clean.py
```

Salida esperada:
```
Battery 1 (Empty stdin) [PASS]
Battery 2 (All 256 single bytes) [PASS]
Battery 2+ (Two-byte corner cases) [PASS]
Battery 3 (Three-byte corner cases & binary permutations) [PASS]

>>> EXTRAORDINARY SUCCESS: ALL 3-STAGE TESTS PASS 100% BIT-FOR-BIT ON mb_ref!
```

### 2. Sintetizar la Quine Récord ($m=281$, 53,562 B)

```bash
# Síntesis determinista (~13 min en Python puro):
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

---

## 🔬 Arquitectura y Fundamentos Matemáticos

### MicroCat (`artifacts/microcat.mal`)

La investigación y telemetría exacta en [`docs/CAT_ANALYSIS.md`](docs/CAT_ANALYSIS.md) demostró 24 teoremas algebraicos sobre el espacio ternario de Olmstead:

1. **Inmunidad Estricta de Memoria Baja ($c < 98$):**
   El cursor de ejecución $c$ arranca en 0 y salta a 98 (aterrizando en 99); todo lazo o retorno aterriza en $\ge 99$. Por lo tanto, ninguna celda en $0..97$ es jamás ejecutada como código.
   - Son 100% inmunes a abortos por caracteres fuera del rango ASCII (`mem[c] < 33 || mem[c] > 126`), pudiendo albergar cualquier valor ternario ($0..59048$).
   - Jamás sufren cifrado determinístico `xlat2`, garantizando que las variables de control y punteros permanezcan 100% invariantes a lo largo de infinitos ciclos.

2. **Discriminador Canónico de 2 Pasos y Monotargets:**
   Con la involución universal de byte $W = 121$ ('y') y constantes ASCII imprimibles $Y_1, Y_2 \in [33, 126]$:
   $$\text{Sep}(x) = \text{crazy}(\text{rot}^k(\text{crazy}(x, Y_1)), Y_2)$$
   Colapsa determinísticamente los 256 valores posibles de byte ($0..255$) a un único destino de salto $T_{\text{byte}}$ con un destino de EOF estrictamente disjunto $T_{\text{eof}} < 98$ (aterrizaje directo en `v` HALT).

3. **Involución sin Pérdida y Tríada de Restauración:**
   $$\forall x \in [0, 255]: \quad \text{crazy}(\text{crazy}(x, 121), 121) \equiv x$$
   $$\text{rot}^{10}(x) \equiv x \quad \forall x \in [0, 59048]$$
   Diez rotaciones sobre la palabra de 10 trits restauran exactamente el estado original de la celda de almacenamiento, permitiendo recuperar el byte exacto para emisión `<` con fidelidad de 8 bits sin tablas de lookup.

4. **Deconstrucción de `cat.mal` (Lutter 2012):**
   El análisis reveló que el preámbulo de 8,905 pasos de Lutter representaba el **96.0%** del archivo original. Su bucle activo requería solo **36 celdas de código distintas** organizadas en 13 pares de instrucciones con saltos inmediatos (`/ i`, `* i`, `p i`, `< i`, `j i`). `microcat.mal` elimina los 8,905 pasos de preámbulo situando las constantes directamente en memoria baja.

### Sintetizador de Quines (`synthesize.py`)

1. **Objetivos**: Se ejecuta la quine de referencia 27,190 pasos y se registran los 215 bytes que la máquina auto-modifica en esa región.
2. **Grafo de 26 macros**: Secuencias de auto-modificación pura encadenadas por búsqueda de Dijkstra sobre valores de la celda 154.
3. **Incremento `DEST+9`**: Búsqueda en runtime (macros duras → BFS acotado $\le 24$ → fallback composite constructivo de 2 escrituras $V \to W \to V+9$).
4. **Capacidad**: El preámbulo debe quedar bajo $94m - 3$; la escalera de valores conocidos es:

| m | Bytes | Estado |
|---|---|---|
| **281** | **53,562** | **Récord Mundial** (verificado con doble motor) |
| 284 | 54,134 | Récord anterior |
| 287 | 54,706 | Escalera verificada |
| 293 | 55,850 | Escalera verificada |
| 308 | 58,709 | Escalera verificada |

---

## 📁 Estructura del Repositorio

```
artifacts/
├── microcat.mal                 ← MicroCat autónomo multi-etapa (3,380 B, PASS Baterías 1..3)
├── cand_three_stage_clean.mal   ← Candidato de 3 etapas verificado bit-a-bit
└── candidate_m281_53562b.mal    ← Quine récord mundial (53,562 B, m=281)

tools/
├── test_three_stage_clean.py    ← Suite de validación exhaustiva de MicroCat
├── build_pipeline_streaming_cat.py ← Ensamblador del pipeline de MicroCat
├── trace_tm.py                  ← Simulador y trazador exacto de VM Malbolge
└── list_loop_cells.c            ← Desensamblador telemétrico de bucles

oracle/
└── mb_ref.c                     ← Intérprete oráculo canónico en C (Olmstead 1998)

docs/
├── CAT_ANALYSIS.md              ← Tratado matemático formal (24 teoremas demostrados)
├── NOTES.md                     ← Bitácora de optimización del sintetizador de quines
└── ROADMAP.md                   ← Frontera de investigación y metas futuras

synthesize.py                    ← Sintetizador CLI determinista de quines
test_corpus.py                   ← Validador del corpus histórico de malbolge.org
Makefile                         ← Build script para oráculo y tests
```

---

## Verificación Independiente y Reproducibilidad

El oráculo `oracle/mb_ref.c` implementa estrictamente la especificación canónica de Ben Olmstead (1998). Para ejecutar la suite completa de pruebas:

```bash
make test              # Compila mb_ref, valida corpus malbolge.org, quines y microcat
```

Evidencia criptográfica de la quine récord:
[`quine_53562_verification.json`](https://github.com/DannyBaanks/Malbolge-MB-Database/blob/master/quine/evidence/quine_53562_verification.json).

---

## Límites Epistémicos (Anti-Fake)

- **MicroCat:** Probado y garantizado al 100% en Baterías 1, 2, 2+ y 3 frente a `oracle/mb_ref.c`. No emite bytes espurios ante EOF.
- **Quines:** El récord de 53,562 B está demostrado contra Lutter y la escalera de parámetros conocidos; m=278 permanece como `NOT_DEMONSTRATED` debido al límite inferior de capacidad del stream sintetizado.
- **Anti-degradación:** La conservación entrópica infinita requiere osciladores de período 2 sobre Ciclo 6 ($F \leftrightarrow J$) o desacople estricto a memoria baja ($c < 98$).

---

## Licencia

MIT — ver [LICENSE](LICENSE). Los programas de referencia de Matthias Lutter (`reference/quine_lutter.malbolge` y `reference/malbolge_org/cat.mal`) se incluyen con atribución histórica como datos de entrada y oráculos de comparación.
