# Auditoría E2E de BolgeForge — 2026-10-20

**Veredicto: los hitos publicados mezclan resultados reales con afirmaciones refutadas y otras no demostradas. La suite verde actual no certifica compatibilidad con Malbolge Clásico.**

Código auditado: `2fe8e8091dae71188ce4d98b8e10199a8a8b783f`.
Auditoría solicitada por Danny. Entorno: Ubuntu/Linux, Python 3.12 y GCC; detalles y hashes de ejecutables en `environment.json`. Se ejecutaron los generadores sobre una extracción de `git archive HEAD` en `/tmp/bolgeforge-audit-20261020/checkout`. Los programas y fuentes publicados se conservaron intactos.

## Dictamen por hito

| Hito del README | Dictamen auditado |
|---|---|
| Quine `m=281`, 53,562 bytes | **DEMONSTRATED**: autorreproducción exacta en intérprete estricto y reconstrucción completa byte por byte. **NOT_DEMONSTRATED**: supremacía mundial absoluta. |
| MicroCat, 3,380 bytes | **REFUTADO como Cat general y programa Clásico admisible**. En el dialecto local reproduce entradas de hasta tres bytes y trunca `ABCD` a `ABC`. El cargador estricto lo rechaza. |
| Truth Machine, supuestamente 105 bytes | **REFUTADO como programa Clásico admisible**. Archivo real: **103 bytes**. La rama `1` también depende de la semántica local alterada para instrucciones no imprimibles. La primacía histórica tiene antecedentes públicos anteriores. |
| Cuatro programas comprimidos | **DEMONSTRATED para los artefactos guardados y los vectores auditados**. Ahorro estructural real: 19,270 caracteres. **Reproducción E2E PARCIAL**: Cat y 99 Bottles se regeneran exactamente; Digital Root y Adder se regeneran incorrectamente. |
| FizzBuzz autónomo, 4,517 bytes / 4,455 celdas | **DEMONSTRATED en el dialecto local**: salida exacta de 413 bytes, cero lecturas de entrada, HALT. **REFUTADO como fuente Clásica admisible**: el cargador estricto lo rechaza. **NOT_DEMONSTRATED**: primero mundial o resolución de un problema abierto. La secuencia se precalcula en Python y se emite linealmente en la VM. |
| Selector Q/C, documento del corpus | **REFUTADO como fuente Clásica admisible**: ambas ramas son rechazadas por el cargador estricto. Los hashes históricos de su evidencia coinciden; eso no demuestra conformidad semántica. |

## Hallazgos que invalidan certificaciones

### A1 · P1 · El oráculo certificado como canónico implementa otro lenguaje

`oracle/mb_ref.c:44–56` solo valida ASCII imprimible. Omite la comprobación original de que cada carácter, en su dirección de carga, decodifique a una de las ocho instrucciones `ji*p</vo`. Un NOP obtenido durante ejecución no equivale a una instrucción admitida por el cargador.

Se compiló por separado un espejo del intérprete de Olmstead de [shinh/ags, commit fijado](https://github.com/shinh/ags/blob/b37fe88ade0d3d862c0500f0b2c0e0f91cc1254e/be/fetcher/malbolge.c), atribuido en su cabecera a Ben Olmstead y puesto en dominio público. Se cotejó la copia local con la descarga HTTPS del mismo commit: iguales al normalizar finales de línea. Procedencia: `strict_mirror_provenance.json`, `sources_primary.json`. La validación imprimible coincide con el [intérprete original enlazado por malbolge.org](https://www.lscheffer.com/malbolge_interp.html).

| Artefacto | Celdas que violan la validación de instrucciones al cargar | Primera dirección inválida | Resultado del espejo estricto |
|---|---:|---:|---|
| `microcat.mal` | 2,918 | 1 | exit 1, `invalid character in source file` |
| `truth_machine.mal` | 82 | 8 | exit 1, mismo error |
| `fizzbuzz.mal` | 3,035 | 1 | exit 1, mismo error |
| `cand_three_stage_clean.mal` | 2,918 | 1 | mismo defecto de admisión |
| `cand_twostroke.mal` | 3,378 | 1 | mismo defecto de admisión |
| Cinco quines y cuatro comprimidos | 0 | — | admisibles |

Evidencia: `loader_scan.json`, `runs/runs.json`, salidas `strict_*` en `runs/`, `selector_Q.stderr`, `selector_C.stderr`.

Además, `oracle/mb_ref.c:67–71` avanza `c` y `d` al encontrar una palabra no imprimible en `mem[c]`; el intérprete original se queda en esa dirección. Esto cambia comportamiento observable. Un modelo separado, con operación ternaria trit a trit, encuentra en la rama `1` de Truth Machine `c=39`, `mem[c]=29490`, después de nueve instrucciones, antes de emitir el primer `1`. Esa transición se congela en la semántica original, pero el oráculo local la salta. Ver `runs/models.json`.

**Corrección necesaria:** restaurar validación y ejecución estrictas como criterio de aceptación. Si se conserva el comportamiento actual para investigación, identificarlo explícitamente como dialecto permisivo y recertificar cada artefacto bajo el lenguaje anunciado.

### A2 · P1 · MicroCat es un eco de tres etapas, no un Cat de flujo

Contra el propio intérprete local, con presupuesto de dos millones de pasos:

```text
stdin ABC   -> stdout ABC, exit 0
stdin ABCD  -> stdout ABC, exit 0
stdin ABCDE -> stdout ABC, exit 0
stdin bytes(0..255) -> solo los tres primeros bytes
```

El modelo separado confirma que `ABCD` alcanza HALT tras 208 instrucciones y **solo tres lecturas**, sin siquiera consumir el cuarto byte (`runs/models.json`). Las pruebas actuales recorren todos los valores posibles de un byte, once pares y dieciséis triples, pero nunca cuatro bytes. Fidelidad del alfabeto no demuestra capacidad de flujo arbitrario.

Evidencia: `microcat_extended.json`, `runs/runs.json`, `microcat_suite.stdout`, `tools/test_microcat_suite.py:24–68`, `tools/test_three_stage_clean.py`.

**Corrección necesaria:** llamarlo prototipo de eco de hasta tres bytes en el dialecto local, o construir y demostrar un ciclo de Cat real. Añadir vectores de longitud 4 y superiores antes de volver a anunciar equivalencia con Cat.

### A3 · P1 · El supuesto bug histórico de EOF no se reproduce en la referencia citada

El README afirma que el `cat.mal` canónico emite `0x88` ante EOF. El archivo incluido, SHA-256 `ce04a6f27b7045b6e0010d6c97873ad8b34ba87c7be6e16d53be0b97a7224a52`, termina limpiamente:

| Entrada | Salida | Telemetría del espejo estricto |
|---|---|---|
| vacía | vacía | HALT, 9,268 iteraciones, una lectura, cero emisiones |
| `A` | `A` | HALT, 9,675 iteraciones, dos lecturas, una emisión |
| `ABCD` | `ABCD` | HALT, 10,896 iteraciones, cinco lecturas, cuatro emisiones |

La instrumentación se conserva en `strict_telemetry.c`; cuenta también la iteración de HALT. Las ejecuciones sin instrumentación confirman idénticas salidas. La [página del autor](https://malbolge.org/cat.html) distingue el Cat corto que no termina del `cat.mal` descargable que sí termina. Son programas distintos.

Evidencia: `cat_eof_telemetry.json`, `runs/`, `reference_strict/`. **Debe retirarse la afirmación de haber corregido ese defecto en el archivo histórico incluido.**

### A4 · P1 · El compresor actual no reconstruye dos de los cuatro artefactos

```text
python3 tools/resynthesize.py all
  cat: reconstrucción byte por byte
  digital_root: AssertionError, generado b'4\xef', esperado b'0\n'
  exit 1

python3 tools/resynthesize.py adder 99_bottles
  adder: AssertionError, generado b'<\x0f', esperado b'0\n'
  exit 1 antes de ejecutar 99_bottles

python3 tools/resynthesize.py 99_bottles
  reconstrucción byte por byte, exit 0
```

Los fallos ocurren con entradas válidas de cero y usando las propias comprobaciones del generador. No se atribuyen al límite de tamaño de operandos. Los archivos fallidos tienen hashes distintos de los publicados y se conservaron como `regenerated_digital_root_compressed.mal` y `regenerated_adder_compressed.mal`.

Evidencia: `resynthesis_all.log`, `resynthesis_remaining.log`, `resynthesis_bottles.log`, `resynthesis_comparison.json`, `regenerated_strict.json`. El espejo estricto tampoco ejecuta correctamente esas regeneraciones (terminación por señal); los artefactos publicados sí funcionan en los controles descritos abajo.

**Corrección necesaria:** localizar y reparar la regeneración; exigir equivalencia funcional y, donde se prometa determinismo, igualdad con los hashes publicados. La mera existencia de los cuatro archivos no demuestra el generador.

### A5 · P2 · Los controles permiten falsos éxitos

Se reprodujeron ambos casos en carpetas nuevas, sin quitar archivos del repositorio:

1. `tools/test_compressed.py`: con los cuatro artefactos ausentes imprime `ALL COMPRESSED BENCHMARKS VERIFIED!` y sale con código 0. Todos los bloques están protegidos por `if p.exists()` y no existe una comprobación final de cantidad.
2. Receta de quines del `Makefile:41–43`: una primera quine deliberadamente incorrecta produce un `diff` fallido, pero una última quine válida deja al bucle con exit 0. Se reprodujo el flujo de la receta cambiando únicamente el archivo temporal a una ruta propia de la prueba. El workflow de GitHub sí usa `set -e` para sus quines; ese punto concreto afecta a `make test`.
3. `mb_ref` devuelve 0 al agotar pasos, incluso con presupuesto cero y sin ejecutar FizzBuzz. Los verificadores no pueden inferir HALT a partir de ese código. `verify_truth_machine_full.py` observa un prefijo finito de salida y lo describe como prueba de infinitud; no comprueba repetición de estado.

Evidencia: `runs/*missing_all_compressed*`, `runs/*broken_first_quine_recipe*`, `runs/*local_zero_fuel*`. La suite real `make test` pasó con exit 0 en esta auditoría (`baseline_tests.json`); los fallos anteriores quedaron fuera de sus condiciones de aceptación.

### A6 · P2 · Primacías y explicaciones exceden la evidencia

- La Truth Machine publicada tiene **103 bytes**, no 105. Ya existe una [solución pública de Malbolge de 90 bytes, publicada el 8 de enero de 2025](https://codegolf.stackexchange.com/questions/62732/implement-a-truth-machine/62947), además de otros antecedentes. La afirmación de ser la primera requiere retirarse.
- `tools/synthesize_fizzbuzz.py:build_fizzbuzz` genera la secuencia en Python y despliega recetas por cada carácter. El programa local emite correctamente la secuencia fija; no decide divisibilidad de 1..100 dentro de la VM. La ausencia de lecturas de stdin está demostrada; ni esa propiedad ni una salida correcta prueban primacía histórica.
- El antecedente de angel_p_57 sí mide 3,590 bytes, realiza 109 lecturas y emite 413 bytes con EOF; se reconstruyó desde el [repositorio del autor, commit fijado](https://github.com/angel-p57/malbolge/tree/b2d278d36e65d66574d435d4cfeb1560b79ed593). Se preservaron fuente, conversor, programa convertido y telemetría. Esa comparación concreta no demuestra que BolgeForge sea el primer Zero-Stdin de la historia.
- “Récord mundial” de quine: se confirmó una quine menor que la referencia y que los otros parámetros incluidos. Una búsqueda bibliográfica y esa escalera no excluyen todas las quines existentes. Redacción defendible: **mejor resultado verificado de esta familia y corpus auditados**.
- Los 59,852 bytes de la referencia con saltos de línea corresponden a la versión de **2015**; la [primera versión de Lutter, de 2012](https://malbolge.org/quine.html), tiene 59,032 bytes sin ese formato. El ahorro de 6,290 bytes compara archivos con formato, no solo instrucciones.
- `docs/CAT_ANALYSIS.md` enlaza seis veces material que existe localmente pero no está versionado, entre ello el ensamblador y el candidato del anillo. No se puede reproducir esa parte desde un checkout limpio (`document_links.json`).

## Lo que sí resistió la auditoría

- **Cinco quines:** `m=281,284,287,293,308` son aceptadas por el espejo estricto y emiten exactamente sus propios archivos; no dependen de aceptar instrucciones iniciales inválidas.
- **Síntesis completa de la quine:** `python3 synthesize.py 281` terminó con exit 0 en la copia limpia y reprodujo los 53,562 bytes con SHA-256 `96b670b825372a0f41fa3b574d47457f92654b76411e5d5be4c438003087610e`. El archivo recién generado volvió a ejecutarse en el espejo estricto, con autorreproducción exacta y exit 0 (`synthesis_m281.log`, `synthesis_m281_result.json`).
- **Corpus histórico:** los ocho programas incluidos fueron ejecutados con el espejo estricto. Las quines históricas se reproducen exactamente; Cat admite los 256 bytes y una secuencia de 4,096 bytes; ROT13 y Hello World cumplen los vectores; 99 Bottles emite 11,459 bytes.
- **Compresión publicada:** los cuatro archivos son admitidos por el espejo estricto. Cat conserva también el flujo binario de 4,096 bytes; Digital Root cumple los vectores auditados; 99 Bottles coincide con toda la salida histórica, no solo con su longitud. El sumador original y el comprimido cumplieron **210/210 ejecuciones** sobre 105 pares dentro del dominio del autor, incluidos ceros y acarreos. La [especificación del sumador](https://malbolge.org/adder.html) limita cada operando a `0..999`, separados por espacio.
- **Integridad histórica:** coincidieron las **47 entradas SHA-256** verificadas en manifiestos del experimento, sumas del selector y tablas de referencias/compresión (`historical_integrity.json`). Es un resultado de integridad de esos archivos, no una validación de todas las conclusiones escritas en ellos.
- **Álgebra limitada:** se verificaron el ciclo único `70↔74`, la involución con 121 en los 256 bytes, las dos identidades de restauración, `rot^10` sobre las 59,049 palabras y el valor del portal 3,312 (`algebra.json`). Estas identidades no certifican por sí solas un programa completo ni la colección de “24 teoremas”.
- **Reconstrucciones pequeñas:** los generadores guardados reproducen exactamente FizzBuzz, Truth Machine y el prototipo de tres etapas (`small_rebuilds.json`). Esto certifica su generación en el dialecto local; no subsana el rechazo del cargador Clásico.

## Reproducir los controles principales

Desde un checkout nuevo del commit auditado, compilar su `mb_ref` con `make`. Compilar el espejo preservado y ejecutar el arnés con un directorio de salida **nuevo**:

```bash
gcc -O2 -Wall -o /tmp/olmstead-strict docs/audits/2026-10-20-e2e/olmstead_strict_mirror.c
python3 docs/audits/2026-10-20-e2e/audit_e2e.py \
  "$PWD" /tmp/olmstead-strict /tmp/bolgeforge-nueva-ejecucion
```

El arnés guarda entrada, salida, stderr, orden, cwd, retorno, duración y hashes para cada proceso. `runs/runs.json` contiene 131 ejecuciones; `baseline_tests.json` registra además los comandos originales de pruebas. Los generadores deben correrse en una copia porque escriben artefactos.

**Control negativo conservado:** el primer arnés incluyó operandos mayores de 999 para el sumador, antes de cotejar su contrato histórico. Fallan tanto el original como el comprimido. Son entradas fuera de contrato y **no** se cuentan como defectos de compresión. La batería corregida está en `adder_domain.json`.

**Intento de auditoría inválido conservado:** unos archivos `strict_reference_*.stdout/stderr` del nivel superior pertenecen a una invocación con raíz equivocada. Se excluyen de las conclusiones. `reference_failed_attempt_note.txt` explica el error; los resultados correctos están en `reference_strict/`.

## Alcance y NOT_DEMONSTRATED

Esta auditoría certifica observaciones sobre el commit y los vectores documentados. No certifica todos los programas posibles, todos los operandos, todos los prototipos ignorados, ni una primacía mundial. No se reescribió evidencia histórica para hacerla concordar con el diagnóstico.

La visita al sitio de Scheffer falló por certificado caducado y posteriormente por timeout; se conserva ese resultado en `sources.json` y `sources_retry.json`. La ejecución independiente utilizó el espejo fijado, descargado por HTTPS y cotejado con su copia local. No se ejecutó CI remoto ni se publicaron cambios.

**Privacidad de evidencia:** Repo Engine bloqueó el primer intento de commit por rutas privadas en `baseline.json`, `runs/runs.json`, `strict_build.stderr` y `strict_mirror_provenance.json`. Esos cuatro originales permanecen intactos localmente y están excluidos de Git mediante el `.gitignore` de esta carpeta. Sus copias `*.public.*` sustituyen únicamente prefijos de rutas por marcadores; son las versiones incluidas en Git. `SHA256SUMS.txt` conserva tanto los compromisos de los originales locales como los de las copias públicas; un checkout público no contendrá esos cuatro originales.

La aceptación final de los hitos necesita corregir A1–A6 y repetir una certificación estricta. Hasta entonces, las etiquetas actuales del README no constituyen una certificación válida de MicroCat, Truth Machine o FizzBuzz en Malbolge Clásico.
