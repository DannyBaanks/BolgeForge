# GUIA-WINDOWS.md — BolgeForge en Windows nativo

## 1. El comando que viniste a ejecutar

En PowerShell, en la raíz del repo:

```powershell
.\build_windows.ps1
```

Salida real (2026-11-05, Windows 11, gcc MinGW-W64 16.1.0, Python 3.12.10):

```text
CC: C:\Users\progr\AppData\Local\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.POSIX.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\bin\gcc.exe
Python: C:\Users\progr\AppData\Local\Programs\Python\Launcher\py.exe -3
Python 3.12.10
--- build mb_ref.exe ---
built C:\Development\ISyCo Git\BolgeForge\mb_ref.exe
--- test-oracle (52 tests) ---
Ran 52 tests in 12.622s
OK
--- test-corpus ---
=== ALL MALBOLGE.ORG CORPUS TESTS PASSED (1.67s) ===
--- test-compressed ---
PASS cat: 7 exact-output cases; strict HALT and reference parity
PASS digital_root: 6 exact-output cases; strict HALT and reference parity
PASS adder: 100 exact-output cases; strict HALT and reference parity
PASS 99_bottles: 1 exact-output cases; strict HALT and reference parity
--- test-quines ---
PASS candidate_m281_53562b.mal: byte-exact self-reproduction and strict HALT
PASS candidate_m284_54134b.mal: byte-exact self-reproduction and strict HALT
PASS candidate_m287_54706b.mal: byte-exact self-reproduction and strict HALT
PASS candidate_m293_55850b.mal: byte-exact self-reproduction and strict HALT
PASS candidate_m308_58709b.mal: byte-exact self-reproduction and strict HALT
--- test-independent ---
PASS independent Olmstead mirror: 236 exact-output comparisons
Mirror source SHA-256: 05abd38e78b266050c5a5e8cc5b36584daa5bbdeb404bfb351de7ea6fa26b510
--- compact-cat --check ---
PASS cat_compact: 7 cases; 7596 cells; handoff 124/124; byte-exact rebuild
ALL WINDOWS CHECKS PASSED
```

Exit code: `0`. No necesitas `make`, `rm`, `/tmp` ni el comando `python3`.

## 2. La regla de oro

**Los `.mal` no se regeneran a ciegas: primero `--check`.** Si un rebuild
difiere de lo publicado, se investiga, no se sobrescribe. Los artefactos
publicados son byte-exactos en Windows y en Linux (`*.mal binary` en
`.gitattributes`); `mb_ref.exe` y `.build/` no se versionan.

## 3. Todos los comandos, uno a uno

### 3.1 Build + certificación (PowerShell)

```powershell
.\build_windows.ps1
```

Qué hace: detecta `gcc`/`cc`/`clang` y Python (`py -3`, luego `python`,
luego `python3`), compila `oracle\mb_ref.c` a `mb_ref.exe` y ejecuta el
equivalente a `make test` (52 tests, corpus, 4 comprimidos, 5 quines,
espejo independiente 236 comparaciones, compact-cat `--check`).
Salida: la de la sección 1. Tiempo: ~15 s.

### 3.2 El mismo build desde `cmd.exe`

```cmd
build_windows.bat
```

Qué hace: delega en `build_windows.ps1` (una sola fuente de lógica).
Salida real (cola):

```text
--- test-quines ---
PASS candidate_m281_53562b.mal: byte-exact self-reproduction and strict HALT
--- test-independent ---
PASS independent Olmstead mirror: 236 exact-output comparisons
--- compact-cat --check ---
PASS cat_compact: 7 cases; 7596 cells; handoff 124/124; byte-exact rebuild
ALL WINDOWS CHECKS PASSED
```

### 3.3 Rebuild de los 4 comprimidos (~5 min en Windows medido: ~11 min)

```powershell
.\build_windows.ps1 -Rebuild
```

Salida real:

```text
--- test-rebuild (~5 min) ---
Compressing cat (handoff 9003)
PASS cat: 7 cases; byte-exact rebuild; {'orig_chars': 9382, 'new_chars': 8254, 'saved_chars': 1128, 'saved_pct': 12.02, 'k': 12, 'delta': 1128, 'end_c': 7822, 'pad_len': 53, 'elapsed_s': 25.5}
Compressing digital_root (handoff 31802)
PASS digital_root: 6 cases; byte-exact rebuild; {'orig_chars': 32136, 'new_chars': 26308, 'saved_chars': 5828, 'saved_pct': 18.14, 'k': 62, 'delta': 5828, 'end_c': 25743, 'pad_len': 231, 'elapsed_s': 67.074}
Compressing adder (handoff 55802)
PASS adder: 100 cases; byte-exact rebuild; {'orig_chars': 56476, 'new_chars': 44914, 'saved_chars': 11562, 'saved_pct': 20.47, 'k': 123, 'delta': 11562, 'end_c': 43973, 'pad_len': 267, 'elapsed_s': 157.646}
Compressing 99_bottles (handoff 22044)
PASS 99_bottles: 1 cases; byte-exact rebuild; {'orig_chars': 22561, 'new_chars': 21809, 'saved_chars': 752, 'saved_pct': 3.33, 'k': 8, 'delta': 752, 'end_c': 21116, 'pad_len': 176, 'elapsed_s': 430.25}
ALL WINDOWS CHECKS PASSED
```

### 3.4 Variante GNU make (solo si tienes MinGW make)

```powershell
mingw32-make -f Makefile.win test
```

Salida real (cola):

```text
py -3 tools/test_quines.py
PASS candidate_m281_53562b.mal: byte-exact self-reproduction and strict HALT
py -3 tools/test_independent.py
PASS independent Olmstead mirror: 236 exact-output comparisons
py -3 tools/build_compact_cat.py --check
PASS cat_compact: 7 cases; 7596 cells; handoff 124/124; byte-exact rebuild
```

Y el ciclo completo, también ejecutado:

```powershell
mingw32-make -f Makefile.win clean
mingw32-make -f Makefile.win all
```

```text
py -3 -c "import pathlib; pathlib.Path('mb_ref.exe').unlink(missing_ok=True); pathlib.Path('.build/sp_solver.dll').unlink(missing_ok=True)"
gcc -O2 -Wall -o mb_ref.exe oracle/mb_ref.c
```

### 3.5 Limpiar y ayuda

```powershell
.\build_windows.ps1 -Clean
.\build_windows.ps1 -Help
```

Salida real de `-Clean`:

```text
removed C:\Development\ISyCo Git\BolgeForge\mb_ref.exe
removed C:\Development\ISyCo Git\BolgeForge\.build\sp_solver.dll
```

### 3.6 Prueba manual del oráculo (opcional)

```powershell
py -3 -c "import subprocess; r=subprocess.run([r'C:\Development\ISyCo Git\BolgeForge\mb_ref.exe', r'C:\Development\ISyCo Git\BolgeForge\reference\malbolge_org\hello_world.mal'], input=b'', capture_output=True); print('rc',r.returncode,'out',r.stdout)"
```

```text
rc 0 out b'Hello, world.'
```

```powershell
py -3 -c "import subprocess; p=bytes(range(256)); r=subprocess.run([r'C:\Development\ISyCo Git\BolgeForge\mb_ref.exe', r'C:\Development\ISyCo Git\BolgeForge\artifacts\cat_compressed.mal'], input=p, capture_output=True, timeout=20); print('rc',r.returncode,'len',len(r.stdout),'exact',r.stdout==p)"
```

```text
rc 0 len 256 exact True
```

```powershell
py -3 -c "import subprocess,pathlib; f=pathlib.Path(r'C:\Development\ISyCo Git\BolgeForge\artifacts\candidate_m281_53562b.mal'); r=subprocess.run([r'C:\Development\ISyCo Git\BolgeForge\mb_ref.exe', str(f),'100000000'], input=b'', capture_output=True, timeout=30); print('rc',r.returncode,'len',len(r.stdout),'expected',len(f.read_bytes()),'exact',r.stdout==f.read_bytes())"
```

```text
rc 0 len 53562 expected 53562 exact True
```

Los hashes publicados no cambian: m281 `96b670b82537…`,
cat_compact `dd8f9b106dd4…` (verificados tras el rebuild).

## 4. Cómo leer la salida

| salida / código | significa | qué hacer |
|---|---|---|
| `ALL WINDOWS CHECKS PASSED`, exit `0` | build + certificación OK en Windows | nada |
| `Ran 52 tests ... OK` | unit tests de `tests/` OK | nada |
| `PASS candidate_m281… byte-exact` | quine reproduce su fuente byte a byte | nada |
| `HANDOFF MATCH` (124/124) | Cat compacto conserva el estado de handoff | nada |
| `FAILED (failures=N)` / `FAILED (exit 1)` en un paso | ese paso falló; el script se detiene ahí | lee el traceback de ese paso, no de los demás |
| `No C compiler found` | falta MinGW-w64 `gcc` en `PATH` | instala gcc y repite |
| `No working Python 3 found` | `py -3`, `python` y `python3` fallan | instala Python 3.10+ y repite |
| `Cannot open …\tmp…` en `test_oracle` | fichero temporal aún abierto (bug ya corregido: `delete=False`) | actualiza el repo |
| `Invalid character` / `INVALID_OPCODE` del oráculo | el `.mal` no es Classic válido | no es un fallo del build; es el loader estricto |

Nota: `unittest` escribe por stderr; en PowerShell eso puede pintarse
como error aunque el exit sea `0`. Manda el exit, no el color.

## 5. Trampas

1. **`python3` en Windows es un stub de la Store** («Python was not
   found»). Usa `py -3` o `python`. El script los prueba en ese orden.
2. **`make` no existe en PowerShell** (solo `mingw32-make` si tienes
   MinGW). Para eso está `build_windows.ps1`/`.bat`, que no necesitan make.
3. **`cc` no existe en Windows** (solo `gcc`). El `Makefile.win` usa
   `CC = gcc` (asignación plana, no `?=`): con `?=` gana el `cc` builtin
   de GNU make y el build falla con «CreateProcess failed».
4. **El binario se llama `mb_ref.exe`, no `mb_ref`.** Los tests lo
   resuelven con `os.name == 'nt'` o con la variable `MB_REF`.
5. **Sin modo binario, Windows corrompe streams:** LF→CRLF (+734 bytes
   en el quine m281) y Ctrl-Z (0x1A) corta la entrada. El oráculo lo
   fija con `_setmode(..., _O_BINARY)` solo en `_WIN32`; en Linux es no-op.
6. **Copiar la carpeta a mano (ZIP) no es clonar con git:** los `.ps1`
   con CRLF crudo fallan al ejecutarse directo (`env: 'python3\r'`)
   y los `.mal` perderían su protección `binary`. Clona con git.
7. **`synthesize.py 281` en Windows: NO PROBADO** (~13 min en Linux;
   la CI de síntesis sigue en `ubuntu-latest`). No lo des por hecho.
8. **`trace_loop` (experiments) es un ELF Linux x86-64**: no se ejecuta
   en Windows. No forma parte de la certificación.

## 6. Qué se verificó y qué no

- Verificado en este host (Windows 11, 2026-11-05): build + 52 tests +
  corpus + comprimidos + quines + independiente + compact-cat, rebuild
  de los 4, `.bat`, `Makefile.win` (clean/all/test), `-Clean`, `-Help`,
  demos manuales. Todo PASS, exit `0`.
- Regresión Linux (Docker `python:3.11`, Debian 13, clone local con los
  cambios): `make test` PASS, espejo SHA `05abd38e…` sin cambios.
- NO PROBADO: CI en GitHub (`windows-native` job, YAML válido pero sin
  run en remoto aún), `synthesize.py 281` en Windows, macOS/ARM.
