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

3. **Truth Machine en Malbolge Clásico: 105 bytes (`artifacts/truth_machine.mal`)**
   - El primer Truth Machine limpio demostrado en la arquitectura canónica de 59,049 celdas.
   - **Bifurcación exacta:** Entrada `'0'` $\to$ emite `'0'` y parada limpia (`v`) en solo 8 pasos de VM; Entrada `'1'` $\to$ ciclo límite cerrado de 3 celdas que emite infinitamente `'1'`s sin degradar la memoria.
   - Verificado formalmente en `oracle/mb_ref.c` mediante [`tools/verify_truth_machine_full.py`](tools/verify_truth_machine_full.py).

4. **Re-síntesis y Compresión de los 4 Grandes de Lutter/Iizawa ($-19,270$ caracteres, $-15.98\%$)**
   - Análisis y optimización estructural del corpus de `malbolge.org` ([`docs/CORPUS_AUDIT.md`](docs/CORPUS_AUDIT.md)), eliminando preámbulos redundantes HeLL:
     - `artifacts/cat_compressed.mal`: **8,254 B** ($-1,128$ B, **$-12.02\%$**)
     - `artifacts/digital_root_compressed.mal`: **26,308 B** ($-5,828$ B, **$-18.14\%$**)
     - `artifacts/adder_compressed.mal`: **44,914 B** ($-11,562$ B, **$-20.47\%$**)
     - `artifacts/99_bottles_compressed.mal`: **21,809 B** ($-752$ B, **$-3.33\%$**)
   - 100% de paridad funcional y regresión bit a bit verificada en [`tools/test_compressed.py`](tools/test_compressed.py).

5. **El Santo Grial: FizzBuzz 100% Autónomo y de Sistema Cerrado (Zero-Stdin) en Malbolge Clásico (4,455 opcodes, 4,517 B, `artifacts/fizzbuzz.mal`)**
   - **Resolución formal del reto histórico:** El primer programa de **sistema cerrado y 100% autónomo** en la especificación canónica de Ben Olmstead (1998, 59,049 celdas) que computa y emite las 100 líneas canónicas de FizzBuzz (`1\n2\nFizz\n4\nBuzz\n...`) y termina con parada limpia (`v`, código 0) con **cero dependencias de stdin**.
   - **Auditoría del Antecedente (angel_p_57, Sep 2023, 3,590 B):** El autor japonés `angel_p_57` publicó en Zenn/GitHub un generador de texto fijo que emite FizzBuzz pero que **ejecuta la instrucción `/` (lectura de stdin) 109 veces** esperando `EOF` ($59,048$) en el acumulador como oráculo para generar constantes. Si se ejecuta en terminal interactiva se congela esperando teclas, y si stdin contiene datos, su salida se corrompe por completo.
   - **Avance de BolgeForge:** Cero llamadas a `/` (**Zero-Stdin**), 100% inmune a la entrada estándar, arquitectura de cinta transportadora lineal con separación estricta de 2,055 celdas entre código ($c \ge 3315$) y datos ($d \le 1259$), y salto cuántico algebraico $\text{crazy}(\text{rot}^2(80), 72) = 3312$. Ejecuta las 100 líneas en **2 ms** sobre `oracle/mb_ref.c`.

---

## Quickstart

```bash
git clone https://github.com/DannyBaanks/BolgeForge.git
cd BolgeForge
make                    # Compila el oráculo de referencia en C (mb_ref)
```

### 1. Ejecutar y Verificar MicroCat (3,380 B)

```bash
# Probar stdin vacío (debe emitir 0 bytes y retornar código 0):
./mb_ref artifacts/microcat.mal < /dev/null
echo "Exit code: $?"

# Probar eco de texto:
echo -n "ABC" | ./mb_ref artifacts/microcat.mal
echo ""

# Ejecutar la suite completa de baterías (256 bytes, pares y secuencias):
python3 tools/test_microcat_suite.py
```

### 2. Probar la Truth Machine (105 B)

```bash
# Caso '0': debe emitir '0' y terminar inmediatamente con exit 0:
echo -n "0" | ./mb_ref artifacts/truth_machine.mal
echo ""

# Caso '1': debe emitir '1' continuamente (cortar con 1,000 pasos de prueba):
echo -n "1" | ./mb_ref artifacts/truth_machine.mal 1000

# Validación automatizada:
python3 tools/verify_truth_machine_full.py
```

### 3. Verificar Benchmarks Comprimidos del Corpus

```bash
python3 tools/test_compressed.py
```

### 4. Ejecutar y Verificar FizzBuzz (4,455 opcodes)

```bash
# Ejecutar las 100 líneas canónicas de FizzBuzz (salida en 2 ms):
./mb_ref artifacts/fizzbuzz.mal

# Validación automatizada bit a bit:
python3 tools/test_fizzbuzz.py
```

### 5. Ejecutar la Suite Completa de Tests

```bash
make test               # Ejecuta corpus malbolge.org, microcat, compressed, truth machine, fizzbuzz y quines
```

### 6. Sintetizar la Quine Récord ($m=281$, 53,562 B)

```bash
# Síntesis determinista (~10-13 min en Python puro):
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

5. **El Teorema de Período 2 ($F \leftrightarrow J$) y el Motor Reversible a Dos Tiempos:**
   - **Unicidad de la Órbita 2 en `xlat2`:** La descomposición cíclica de la permutación de cifrado determinista `xlat2` de Ben Olmstead demuestra que existe **exactamente una única órbita de longitud 2** en todo el alfabeto ASCII imprimible $[33, 126]$: los caracteres $\{70, 74\}$ (`'F'` y `'J'`). Todas las demás órbitas poseen longitudes 4, 5, 6, 9 o 68.
   - **Bifurcación Activo/Pasivo Inmune:** Al espaciar las 14 instrucciones del Discriminador y las 20 celdas de la Rutina de Salida en residuos canónicos módulo 94 inicializados con `ord('F')` (70), el circuito adquiere dinámica bi-fásica estricta:
     - **Pase Activo (Estado 70):** Ejecuta las operaciones computacionales (`/`, `j`, `p`, `*`, `<`, `i`) y muta determinísticamente a 74.
     - **Pase de Barrido y Recarga (Estado 74):** Los 14 residuos decodifican a instrucciones puramente pasivas y sin efectos colaterales (`P`, `E`, `r`, `M`, `'`), permitiendo que el cursor $c$ atraviese el circuito recargando todas las celdas nuevamente a 70 sin colisiones ni emisiones espurias.
   - **Tríada de Auto-Reset Algebraico Involutivo:**
     $$\forall b \in [0, 255], \quad w = \text{crazy}(b, 121): \quad \text{crazy}(\text{crazy}(121, w), \text{crazy}(121, w)) \equiv 121$$
     $$\forall b \in [0, 255]: \quad \text{crazy}(\text{crazy}(121, b), \text{crazy}(121, b)) \equiv 121$$
     Dos aplicaciones sucesivas de la operación `p` con $A=121$ colapsan tanto el byte recuperado como su representación intermedia en memoria exactamente a 121 con cero excepciones a lo largo de todo el espacio de 8 bits, demostrando la posibilidad teórica de un bucle infinito cerrado sin consumo de memoria.

### FizzBuzz Autónomo (`artifacts/fizzbuzz.mal`)

La síntesis de FizzBuzz sobre el toro de 59,049 celdas resuelve un problema abierto desde 1998 mediante cuatro principios formales:

1. **Arquitectura de Cinta Transportadora (Conveyor Architecture):**
   Para evitar que el puntero de datos $d$ sobreescriba instrucciones de código ejecutables $c$, la memoria se particiona en dos regiones disjuntas separadas por una brecha estéril de 2,055 celdas:
   $$\text{Datos: } d \in [121, 1259] \quad \ll \quad \text{Código: } c \in [3315, 4454]$$
   Dado que en cada ciclo de Malbolge tanto $c$ como $d$ se incrementan en 1 tras cada instrucción, se mantiene la invariante de sincronía:
   $$\Delta c \equiv \Delta d$$
   Esto garantiza que cada macro de emisión consume exactamente la misma cantidad de celdas de código que de celdas de datos, manteniendo constante la distancia relativa durante toda la ejecución.

2. **Salto Cuántico a Memoria Alta sin Literales Prohibidos:**
   El cargador de Malbolge solo admite caracteres en ASCII $[33, 126]$. No es posible codificar literales $> 126$ como 3312 directamente en el archivo fuente. El preámbulo en memoria baja ($c=0 \to 99..107$) computa algebraicamente el salto:
   $$\text{crazy}(\text{rot}^2(80), 72) = 3312$$
   Aterriza en el cojín de amortiguación $c=3312..3314$, configurando $d=121$ antes de ingresar a la cinta en $c=3315$.

3. **Matriz de Recetas de Emisión de Caracteres:**
   Las 100 líneas contienen 413 bytes distribuidos en exactamente 15 caracteres únicos (el `'0'` nunca se emite):
   - **Salto de Línea (`\n`, ASCII 10):** Emitido en 1 paso mediante rotación: $\text{rot}(118) \equiv 19722 \equiv 10 \pmod{256}$. Secuencia: `* <` (2 opcodes, 2 celdas de datos).
   - **Dígitos ($1..9$) y Letras ($B, F, i, u, z$):** Emitidos en 2 pasos mediante composición $\text{crazy}(\text{rot}(V_1), V_2) \pmod{256}$. Secuencia: `* p <` (3 opcodes, 3 celdas de datos).
   - Cada constante $V_1, V_2$ está garantizada dentro de ASCII imprimible $[33, 126]$.

4. **Parada Limpia (`v`):**
   Al alcanzar el carácter 413 (el `\n` tras el número 100 `"Buzz\n"`), el cursor de instrucciones aterriza directamente en el opcode de terminación limpia `v` en $c=4454$, saliendo inmediatamente con código 0 y cero bytes espurios.

5. **Auditoría Comparativa: angel_p_57 (Sep 2023) vs BolgeForge (Oct 2026):**
   En septiembre de 2023, el autor `angel_p_57` publicó en Zenn/GitHub ([`angel-p57/malbolge`](https://github.com/angel-p57/malbolge)) una herramienta (`mksrc4fixed.rb`) para emitir texto fijo que generó un FizzBuzz de 3,590 bytes. La auditoría formal mediante trazado telemétrico en `mb_ref` reveló diferencias arquitectónicas fundamentales:

   | Métrica | angel_p_57 (2023) | BolgeForge (2026) |
   |---|---|---|
   | **Tamaño** | 3,590 bytes | 4,455 opcodes (4,517 B envuelto) |
   | **Metodología** | Generador de texto fijo | Cinta transportadora lineal ($\Delta c \equiv \Delta d$) |
   | **Llamadas a Stdin (`/`)** | **109 lecturas de entrada** | **0 (Cero)** |
   | **Autonomía (Sistema Cerrado)** | ❌ Requiere stdin en EOF | ✅ **100% Autónomo y autocontenido** |
   | **Inmunidad ante Stdin** | ❌ Se cuelga en terminal / corrompe salida | ✅ **Inmune** (idéntico con o sin stdin) |
   | **Salto Cuántico** | Salto HeLL estándar | Salto algebraico $\text{crazy}(\text{rot}^2(80), 72) = 3312$ |
   | **Brecha de Inmunidad** | Variable | 2,055 celdas estériles ($d \le 1259 \ll c \ge 3315$) |

   *Mecanismo del oráculo de angel_p_57:* En Malbolge, la instrucción `/` ante EOF asigna $59,048$ al acumulador $A$. El generador de 2023 usó esto 109 veces como atajo para inyectar $59,048$ ($2222222222_3$). Al ejecutarse en una terminal interactiva sin `< /dev/null`, el proceso se bloquea esperando entradas; y si stdin recibe cualquier carácter, la salida se destruye (`Ftzz`, `1wBl||`, etc.). BolgeForge resuelve el problema mediante síntesis aritmética pura sin tocar el flujo de entrada jamás.

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
├── fizzbuzz.mal                 ← FizzBuzz autónomo 1..100 en Classic Malbolge (4,455 opcodes, 4,517 B)
├── microcat.mal                 ← MicroCat autónomo multi-etapa (3,380 B, PASS Baterías 1..3)
├── truth_machine.mal            ← Truth Machine canónica en Classic Malbolge (105 B)
├── cat_compressed.mal           ← Cat de Lutter re-sintetizado (-12.02%, 8,254 B)
├── digital_root_compressed.mal  ← Digital Root re-sintetizado (-18.14%, 26,308 B)
├── adder_compressed.mal         ← Adder re-sintetizado (-20.47%, 44,914 B)
├── 99_bottles_compressed.mal    ← 99 Bottles re-sintetizado (-3.33%, 21,809 B)
└── candidate_m281_53562b.mal    ← Quine récord mundial (53,562 B, m=281)

tools/
├── synthesize_fizzbuzz.py       ← Sintetizador formal de la arquitectura de cinta transportadora
├── test_fizzbuzz.py             ← Suite de verificación formal bit a bit de FizzBuzz frente a mb_ref
├── test_microcat_suite.py       ← Suite de 4 baterías (0, 1, 2, 3 bytes) para MicroCat
├── verify_truth_machine_full.py ← Verificador formal de bifurcación de la Truth Machine
├── test_compressed.py           ← Suite de verificación de los 4 benchmarks comprimidos
├── test_three_stage_clean.py    ← Ensamblador y validador de las 3 etapas de MicroCat
├── resynthesize.py              ← Compresor de preámbulos HeLL y solucionador Dijkstra
├── trace_tm.py                  ← Simulador y trazador exacto de VM Malbolge
└── list_loop_cells.c            ← Desensamblador telemétrico de bucles

reference/
└── malbolge_org/                ← Corpus histórico completo de 8 programas (Lutter, Iizawa, Cooke)

oracle/
└── mb_ref.c                     ← Intérprete oráculo canónico en C (Olmstead 1998)

docs/
├── CAT_ANALYSIS.md              ← Tratado matemático formal (24 teoremas demostrados)
├── CORPUS_AUDIT.md              ← Auditoría y telemetría exacta de los programas de malbolge.org
├── NOTES.md                     ← Bitácora de optimización del sintetizador de quines
└── ROADMAP.md                   ← Frontera de investigación y metas futuras

synthesize.py                    ← Sintetizador CLI determinista de quines
test_corpus.py                   ← Validador del corpus histórico de malbolge.org
Makefile                         ← Build script para oráculo y tests integrados
```

---

## Verificación Independiente y Reproducibilidad

El oráculo `oracle/mb_ref.c` implementa estrictamente la especificación canónica de Ben Olmstead (1998). Para compilar y ejecutar la suite completa de pruebas:

```bash
make test              # Compila mb_ref y ejecuta:
                       # 1. test-corpus (8 programas de malbolge.org)
                       # 2. microcat (fundamentos + 4 baterías)
                       # 3. test-compressed (cat, digital_root, adder, 99_bottles)
                       # 4. test-tm (bifurcación de la Truth Machine)
                       # 5. test-fizzbuzz (emisión canónica de 100 líneas, 413 B)
                       # 6. quines (autorreproducción byte por byte de la escalera)
```

Evidencia criptográfica de la quine récord:
[`quine_53562_verification.json`](https://github.com/DannyBaanks/Malbolge-MB-Database/blob/master/quine/evidence/quine_53562_verification.json).

---

## Límites Epistémicos (Anti-Fake)

- **FizzBuzz:** Reconocemos formalmente el trabajo previo de angel_p_57 (septiembre 2023, 3,590 B) como el primer generador de texto fijo de FizzBuzz en Malbolge bajo la precondición de stdin vacío (`< /dev/null`). El logro demostrado de BolgeForge (4,455 opcodes) es la primera implementación 100% autónoma y de sistema cerrado (**Zero-Stdin**), libre de llamadas a `/`, inmune a la entrada estándar y ejecutable en cualquier terminal o entorno interactivo sin oráculos externos.
- **MicroCat:** Probado y garantizado al 100% en Baterías 1, 2, 2+ y 3 frente a `oracle/mb_ref.c`. No emite bytes espurios ante EOF.
- **Quines:** El récord de 53,562 B está demostrado contra Lutter y la escalera de parámetros conocidos; m=278 permanece como `NOT_DEMONSTRATED` debido al límite inferior de capacidad del stream sintetizado.
- **Anti-degradación:** La conservación entrópica infinita requiere osciladores de período 2 sobre Ciclo 6 ($F \leftrightarrow J$) o desacople estricto a memoria baja ($c < 98$).

---

## Licencia

MIT — ver [LICENSE](LICENSE). Los programas de referencia de Matthias Lutter (`reference/quine_lutter.malbolge` y `reference/malbolge_org/cat.mal`) se incluyen con atribución histórica como datos de entrada y oráculos de comparación.
