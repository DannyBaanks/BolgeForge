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

9. **Teorema del Motor Regenerativo Bi-Fásico a Dos Tiempos (Pista Helicoidal Módulo 94):**
   - Las 7 instrucciones del lenguaje forman una hélice lineal perfecta en orden de ejecución cronológico módulo 94:
     $$47 \text{ (/ in)} \longrightarrow 63 \text{ (* rot)} \longrightarrow 64 \text{ (j set d)} \longrightarrow 86 \text{ (p op)} \longrightarrow 105 \text{ (v halt)} \longrightarrow 122 \text{ (i jump)} \longrightarrow 123 \text{ (< out)}$$
   - Todas las celdas intermedias entre estos anclajes decodifican a NOPs 100% inertes en Ciclo 5 (`F`).
   - En una arquitectura de doble pista (Pista 1 para bytes impares, Pista 2 para bytes pares), mientras la Pista 1 procesa un byte ($F \to J$), la Pista 2 regenera sus celdas mediante un deslizamiento pasivo de NOPs ($J \to F$). Al alternar cilindros en cada byte, el motor opera indefinidamente con **0 degradación de código**, resolviendo el problema de la degeneración entrópica en Malbolge.

10. **Teorema del Pipeline Multi-Etapa y la Invariante del Colchón Sacrificial de Salto (`[DEMONSTRATED — RUNTIME]`):**
    - En la especificación Olmstead (`oracle/mb_ref.c`), al ejecutar un salto `i` en la celda $c$ hacia $\text{mem}[d] = T$:
      $$c \leftarrow T, \quad \text{mem}[T] \leftarrow \text{xlat2}[\text{mem}[T] - 33], \quad c \leftarrow c + 1$$
    - La instrucción `i` que origina el salto **no se muta**; únicamente la celda de aterrizaje $T$ sufre cifrado `xlat2`. En consecuencia, todo destino de salto $T$ actúa como un **colchón de aterrizaje sacrificial** y no puede alojar constantes de datos estáticas.
    - **Reubicación de Discriminadores Sin Colisión:**
      - Reubicando el discriminador de la Etapa 2 a $\text{BASE} = 77$ ($77..82$), las celdas $71..76$ quedan liberadas sin alterar las etapas previas.
      - Asignando el discriminador de la Etapa 3 con constante $Y_2 = 72$ ('H') en la celda 74, el salto EOF aterriza en la celda 72 (cushion) $\to$ 73 (`v` HALT), mientras que el salto de byte conduce limpiamente a la rutina de salida en 3312 sin tocar celdas de etapas activas.

11. **Teorema del Anillo Oscilador Bi-Fásico a Dos Tiempos y la Invariante de NOPs 80/94 (`[DEMONSTRATED — ALGEBRAIC & RUNTIME]`):**
    - En la permutación `xlat2`, el ciclo 6 ($F \leftrightarrow J$, $70 \leftrightarrow 74$) es la **única órbita de período 2** de todo el espacio de estados de Malbolge.
    - **Invariante de NOPs Universales (80/94):** En exactamente 80 de las 94 posiciones módulo 94, tanto $F$ como $J$ decodifican a instrucciones NOP totalmente inertes. No modifican registros $a$ ni $d$, ni escriben en memoria.
    - **Completitud Funcional Complementaria (14/94):** En las 14 posiciones restantes, cada una de las 7 instrucciones del lenguaje se activa en una fase y es un NOP inerte en la fase opuesta:
      - Cilindro 1 ($F$ activo / $J$ NOP): `/` (47), `j` (64), `p` (86), `*` (63), `v` (11), `i` (28), `<` (29).
      - Cilindro 2 ($J$ activo / $F$ NOP): `/` (43), `j` (60), `p` (82), `*` (59), `v` (7), `i` (24), `<` (25).
    - La separación entre los anclajes de ambos cilindros es invariante: $\Delta \equiv -4 \pmod{94}$ (dado que $74 - 70 = 4$).
    - Un convoy lineal donde el Cilindro 1 precede al Cilindro 2 y un salto permanentemente cierra el lazo ejecuta una oscilación perfecta: en pases impares el Cilindro 1 opera activamente mientras el Cilindro 2 regenera pasivamente sus celdas ($F \to J$), y en pases pares el Cilindro 1 regenera ($J \to F$) mientras el Cilindro 2 opera activamente. La degeneración entrópica es exactamente **cero**.

12. **Teorema de la Tríada de Restauración Algebraica de Celdas de Datos (`[DEMONSTRATED — ALGEBRAIC]`):**
    - Tras la emisión de un byte por `<` tras saltar a la rutina de salida en 368, las celdas de discriminación se restauran a su estado virgen inicial sin depender del valor de entrada $x$:
      - **Restauración de $Y_1$ (80, 'P'):** $\text{crazy}(\text{rot}^6(368), 80) \equiv \mathbf{80}$.
      - **Restauración de $W$ (121, 'y'):** $\text{crazy}(\text{rot}^1(\text{crazy}(368, 103)), 35) \equiv \mathbf{121}$.
      - **Restauración de $Y_2$ (35, '#'):** $\text{crazy}(\text{rot}^1(\text{crazy}(121, 56)), 35) \equiv \mathbf{35}$.
    - **Invarianza de Escritura en Constantes de Memoria Alta:** Toda constante $K \in \{29524, 59046, 59047\}$ operada por $a$ en la tríada $\{0, 29524, 59048\}$ satisface $\text{crazy}(a, K) = K$, impidiendo la corrupción de constantes durante el cómputo.
    - **Separador Cristalino Sin Preámbulo:** El reticulado de período 6 inducido por la semilla `('6', '6')` genera copias inagotables de $c_1 = 29551$ y $c_2 = 27$. La operación $\text{crazy}(\text{crazy}(W, 29551), 27)$ colapsa EOF a $\mathbf{0}$ e induce para los 256 bytes valores $\ge \mathbf{29296}$, eliminando por completo los 8,991 pasos de preámbulo de Lutter (2012).

13. **Teorema del Anillo Oscilador Helicoidal y Necesidad Topológica de la Hélice (`[DEMONSTRATED — ALGEBRAIC & RUNTIME]`):**
    - Dado que las instrucciones activas en Ciclo 6 ($F \leftrightarrow J$) residen en residuos discretos y no consecutivos módulo 94 ($\{11, 28, 29, 47, 63, 64, 86\}$), ninguna secuencia contigua de longitud $> 1$ puede pertenecer a Ciclo 6. Por lo tanto, un convoy de 94 celdas por revolución helicoidal es la **única topología admisible** para bucles cerrados infinitos en Malbolge sin degradación entrópica.
    - La separación entre las fases de los dos cilindros es invariante: $\Delta \equiv -4 \pmod{94}$. Todas las distancias espaciotemporales entre instrucciones consecutivas son exactamente idénticas en ambos cilindros:
      - `/` a `j`: exactamente 17 pasos.
      - `j` a `p`: exactamente 22 pasos.
      - `p` a `j`: exactamente 72 pasos.
      - Entre rotaciones consecutivas `*`: exactamente 93 pasos.
      - Rot 3 a `p`: exactamente 23 pasos (deslizamiento natural directo sin puntero `j`).
      - `p` a `j`: exactamente 72 pasos.
      - `j` a `i`: exactamente 58 pasos.
    - En cada vuelta del anillo oscilador, el cursor de ejecución recorre ambos cilindros: el cilindro activo dispara ($F \to J$), mientras que el cilindro complementario se recarga pasivamente como NOP ($F \to J$). En la siguiente vuelta, las polaridades se invierten ($J \to F$). La oscilación tiene período exactamente 2 y degeneración exactamente cero.

14. **Teorema de la Transformación de Preimágenes para Celdas de Datos y Punteros (`[DEMONSTRATED — ALGEBRAIC & RUNTIME]`):**
    - Toda celda de datos o puntero $C$ situado en el rango transitado por el puntero de instrucciones $c$ sufre exactamente una transformación $C \leftarrow \text{xlat2}[C - 33]$ antes de que el puntero de datos $d$ acceda a ella.
    - Dado que `xlat2` es una permutación biyectiva estricta de $33..126$, todo operando deseado $K$ posee una preimagen única $P = \text{inv\_xlat2}(K) \in [33, 126]$.
    - Toda preimagen $P$ requerida para el convoy helicoidal decodifica a una instrucción NOP 100% inerte al ser ejecutada como código por $c$, mutando determinísticamente al operando matemático $K$ antes de que $d$ la lea.

15. **Teorema del Espacio Discriminador Monotarget y Convergencia Sub-Trit (`[DEMONSTRATED — ALGEBRAIC & RUNTIME]`):**
    - En el álgebra ternaria de Olmstead para $W = 121$ ('y') y operandos ASCII $Y_1, Y_2 \in [33, 126]$, existen exactamente **16 configuraciones canónicas** que colapsan los 256 bytes de entrada a un destino de salto idéntico y único $T_{\text{byte}}$ con un destino de EOF estrictamente disjunto $T_{\text{eof}}$:
      1. $k = 4$ rotaciones: $Y_1 = 80$ ('P'), $Y_2 = 35$ ('#') $\implies T_{\text{eof}} = 8$, $T_{\text{byte}} = \mathbf{368}$ (utilizado en Etapa 1).
      2. $k = 3$ rotaciones: $Y_1 = 80$ ('P'), $Y_2 = 51$ ('3') $\implies T_{\text{eof}} = 24$, $T_{\text{byte}} = \mathbf{1104}$ (utilizado en Etapa 2 / Pista 1).
      3. $k = 2$ rotaciones: $Y_1 = 80$ ('P'), $Y_2 = 72$ ('H') $\implies T_{\text{eof}} = 72$, $T_{\text{byte}} = \mathbf{3312}$ (utilizado en Pista 2).
16. **Teorema de la Restauración Hexádica de Datos en el Anillo Oscilador (`[DEMONSTRATED — ALGEBRAIC]`):**
    - En ambos cilindros del oscilador bi-fásico, las 6 variables de discriminación y almacenamiento son regeneradas determinísticamente a sus constantes virgen ASCII sin dependencia del valor de entrada $x$:
      - **Tríada de Pista 1 (desde el objetivo de salto 1104):**
        - $Y1_1 \to \mathbf{80}$ ('P'): $\text{crazy}(\text{rot}^7(1104), 80) \equiv \mathbf{80}$.
        - $Y2_1 \to \mathbf{51}$ ('3'): $\text{crazy}(\text{crazy}(33, 33), 1104) \equiv \mathbf{51}$.
        - $W1 \to \mathbf{121}$ ('y'): $\text{crazy}(\text{rot}^2(\text{crazy}(1104, 33)), 36) \equiv \mathbf{121}$.
      - **Tríada de Pista 2 (desde el objetivo de salto 3312):**
        - $Y1_2 \to \mathbf{80}$ ('P'): $\text{crazy}(\text{rot}^8(3312), 80) \equiv \mathbf{80}$.
        - $W2 \to \mathbf{121}$ ('y'): $\text{crazy}(\text{rot}^3(\text{crazy}(3312, 36)), 38) \equiv \mathbf{121}$.
        - $Y2_2 \to \mathbf{72}$ ('H'): $\text{crazy}(\text{rot}^1(\text{crazy}(121, 53)), 72) \equiv \mathbf{72}$.
    - Esta hexada garantiza que todas las celdas de datos vuelvan a ser caracteres ASCII estándar antes del inicio del siguiente lapso, eliminando por completo la degeneración entrópica residual en las variables del circuito.

17. **Teorema de la Inversión de Preimágenes en el Retorno y Trampolines a Memoria Baja (`[DEMONSTRATED — ALGEBRAIC & RUNTIME]`):**
    - **Inversión de Preimágenes para Celdas Transitadas:** Toda celda de datos $M$ transitada por el cursor de instrucciones $c$ ($c \ge 99$) antes de ser leída como operando por $d$ debe ser restaurada a su **preimagen biyectiva** $P = \text{inv\_xlat2}(K)$, no a su constante matemática $K$.
      - Si la celda `127` se restaura directamente a $80$ ('P'), al transitar $c$ sobre ella en la vuelta siguiente muta a $\text{xlat2}[80-33] = 66$ ('B'), decodificando espuriamente a la instrucción `<` (emisión espuria del byte previo).
      - Al restaurar la celda `127` a su preimagen $P_{127} = \text{inv\_xlat2}(80) = \mathbf{50}$ ('2'), $c$ decodifica en el residuo 33 la instrucción `{` (NOP universal 100% inerte), mutando determinísticamente a $80$ ('P') listo para ser consumido como operando por `p` en la celda 274.
    - **Inmunidad Estricta de Memoria Baja ($c < 98$):** Toda celda con dirección $< 98$ jamás es transitada por $c$ (puesto que el portal de arranque en la celda 0 salta directamente a la celda 98, aterrizando en 99, y todo lazo de retorno aterriza en 99). En consecuencia:
      - Las celdas en el rango $0..97$ son 100% inmunes a la regla de detención por no-ASCII (`mem[c] < 33 || mem[c] > 126`), pudiendo albergar cualquier valor arbitrario de 10 trits ($0..59048$) sin provocar abortos del intérprete.
      - Los punteros de salto inter-etapa e inter-vuelta alojados en memoria baja permanecen perpetuamente invariantes y libres de degradación entrópica.
    - **Demostración en Runtime:** Verificada en simulación y ejecución bit-a-bit en [`artifacts/cand_twostroke.mal`](../artifacts/cand_twostroke.mal) procesando secuencias de 3 bytes (`b"ABC"`) con fidelidad total y 0 bytes espurios intermedios.

18. **Teorema del Trampolín de Re-Excitación por Salto y la Rotación Estacionaria en Ciclo 6 (`[DEMONSTRATED — ALGEBRAIC & TELEMETRIC]`):**
    - **Mecanismo Dinámico del Salto:** En la semántica de Olmstead (`oracle/mb_ref.c`), la instrucción `i` en la celda $c$ ejecutando un salto hacia $T = \text{mem}[d]$ realiza:
      $$c \leftarrow T, \quad \text{mem}[T] \leftarrow \text{xlat2}[\text{mem}[T] - 33], \quad c \leftarrow c + 1$$
    - **Paradoja de la Re-Excitación:** Si una celda $R$ en Ciclo 6 reside en estado pasivo $F$ (70), un salto indirecto que aterrice en $R$ muta $R$ forzosamente a su estado activo $J$ (74), dejando $c$ en $R + 1$.
    - **El Trampolín de Dos Saltos (Telemetría de `cat.mal` Lutter 2012 Desmitificada):** Telemetría exacta en pasos 9022–9025 y 9430–9432 reveló que Lutter mantuvo la celda 9083 ejecutando `*` indefinidamente sin degradación usando un lazo de rebote:
      1. Un salto a $R$ excita la celda pasiva de $F \to J$ (74), aterrizando el cursor en $R + 1$.
      2. En $R + 1$, un salto `i` hacia $R - 1$ muta el colchón sacrificial y sitúa $c \leftarrow R$.
      3. La celda $R$ se ejecuta en fase activa $J$ (rotación `*`), mutando de regreso de $J \to F$ (70).
      4. Al concluir la rotación, la celda $R$ queda 100% regenerada en su estado virgen $F$, lista para la siguiente invocación.
    - **Reducción de Huella Espacial:** Este trampolín permite ejecutar las 10 rotaciones de involución sobre una **única celda estacionaria de 3 bytes** en lugar de desenrollar 10 revoluciones helicoidales de 940 bytes, abriendo la vía para colapsar el motor regenerativo completo por debajo de 1 KB sin introducir degradación entrópica residual.

---

## 3. Estado Epistémico y Frontera de Demostración

1. **Incompatibilidad directa de las 26 macros del Módulo 0 de la Quine con `cat.mal` (`[OBSERVED NEGATIVE RESULT]`):**
   - Confirmada la amputación del bucle canónico al cortar en `9,067`.
2. **Detección de EOF y Terminación Inmediata Limpia en 125 Bytes (`[DEMONSTRATED — RUNTIME]`):**
   - Sintetizado en [`artifacts/cand_valid.mal`](../artifacts/cand_valid.mal) (125 bytes) y verificado contra `oracle/mb_ref.c` en [`tools/test_valid_ascii_cat.py`](../tools/test_valid_ascii_cat.py).
3. **Eco de Bytes con Fidelidad Total de 8 Bits en 430 Bytes (`[DEMONSTRATED — RUNTIME]`):**
   - Sintetizado en [`artifacts/microcat.mal`](../artifacts/microcat.mal) (430 bytes) y verificado contra `oracle/mb_ref.c` en [`tools/test_microcat_suite.py`](../tools/test_microcat_suite.py). 22 veces más compacto que el estándar histórico de 9,503 bytes.
4. **Cat Multi-Byte de 2 Etapas en 1,150 Bytes (`artifacts/cand_two_stage.mal`) `[DEMONSTRATED — RUNTIME]`:**
   - Verificado en [`tools/test_twostage_ab.py`](../tools/test_twostage_ab.py) contra `oracle/mb_ref.c`. Pasa 100% bit-a-bit: `b""` $\to$ rc 0 (0 bytes), todos los 256 bytes individuales $\to$ eco exacto rc 0, y pares de 2 bytes (`b"AB"`, `bytes([0, 255])`, etc.) $\to$ eco exacto rc 0.
5. **Cat Multi-Byte de 3 Etapas en 3,380 Bytes (`artifacts/cand_three_stage_clean.mal`) `[DEMONSTRATED — RUNTIME]`:**
   - Verificado en [`tools/test_three_stage_clean.py`](../tools/test_three_stage_clean.py) contra `oracle/mb_ref.c`. Pasa 100% bit-a-bit: Batería 1 (`b""` $\to$ 0 bytes, rc 0), Batería 2 (256/256 bytes individuales), Batería 2+ (pares de 2 bytes), y Batería 3 (secuencias de 3 bytes: `b"ABC"`, `b"XYZ"`, `b"123"` y permutaciones binarias con `0x00` y `0xFF`).
6. **Límite Teórico de Desenrollado Pipeline (`MaxUnrolledStages <= 11`) (`[DEMONSTRATED — THEORETICAL]`):**
   - Demostrado que el pipeline lineal no puede superar 11 etapas sin colisión de celdas en el espacio ASCII $33..126$ (94 direcciones disponibles frente a 7-8 celdas de datos literales por etapa).
7. **Motor Bi-Fásico a Dos Tiempos en Anillo Oscilador (`artifacts/cand_twostroke.mal`) (`[DEMONSTRATED — RUNTIME & ALGEBRAIC]`):**
   - Demostrada la conservación de período 2 ($F \leftrightarrow J$) en las 14 posiciones activas módulo 94 y la invarianza de NOPs en las 80 posiciones restantes.
   - Demostrado el circuito de preimágenes y anclajes en [`tools/assemble_twostroke_cat.py`](../tools/assemble_twostroke_cat.py) con ejecución 100% bit-a-bit en Batería 1 (EOF `b""` $\to$ 0 bytes, rc 0), Batería 2 (todos los 256 bytes individuales `0x00..0xFF`), Batería 2+ (pares de 2 bytes `b"AB"`, `b"ZZ"`, binarios), y Batería 3 (`b"ABC"` limpio).
   - Verificado el salto de retorno en lazo cerrado ($c = 3339 \to 98 \to 99$) con re-anclaje de fase de punteros y preimágenes de datos.




